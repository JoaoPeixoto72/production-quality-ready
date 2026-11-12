#!/usr/bin/env python3
"""run_all_owners — run the instruments the plugin can run for the owners declared
in gates.json, filtered by the project's `platform`, and write
`.audit/<owner>/<producer>--<check>.evidence.yaml`.

Contract (CONTRACTS §4.6): a `result: PASS` is written ONLY for a check this
script executed, and every PASS carries `command:` and `log:` pointing at the
captured output. Anything it cannot run is written as
`NOT_VERIFIED / missing-instrument` with the reason — the gap is declared, never
filled. Then it applies the gates (apply_gates.py) and prints the verdict.

Runs outside the model (CI or by hand), on any OS with Python 3.9+ and git;
node only for the website owner. Installs nothing.

Usage:
  python run_all_owners.py --repo .
  python run_all_owners.py --repo . --only code-audit,security-audit
  python run_all_owners.py --repo . --skip commercial-readiness
  python run_all_owners.py --repo . --dry-run
  python run_all_owners.py --repo . --website-url https://example.com

Exit: the exit code of apply_gates.py (0 gates open, 1 a gate closed, 2 cannot
judge); 2 also when gates.json is missing or has no platform.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE = HERE.parent
AUDIT_APP = CORE / "skills" / "audit-app" / "scripts"
sys.path[:0] = [str(AUDIT_APP), str(HERE)]
import validate_evidence as ve  # noqa: E402
from workspace import unprepared  # noqa: E402

PRODUCER_SCRIPT = "plugins/production-quality-ready/scripts/run_all_owners.py"
OWN_STAMP = re.compile(r"^\s*producer-script:\s*\S*run_all_owners\.py\s*$", re.M)
TIMEOUT = 1800
CANNOT_RUN = 77  # a declared command's "I could not measure here" (the harness skip code): never a FAIL
# Every `adapter-hints` key this runner reads, and what it settles (CONTRACTS §7.5.4). A project
# that names its command differently gets a check that can never close, so the table is the contract.
HINTS = {
    "build-command": "code-audit :: runtime.build-passes",
    "typecheck-command": "code-audit :: runtime.types-check",
    "tests-command": "code-audit :: runtime.tests-pass",
    "smoke-command": "verify :: smoke-test-passes",
    "design-pro-capture-command": "design-pro :: a11y-critical-flows",
    "tenant-isolation-command": "security-audit :: sec.tenant-isolation",
    "migrations-verify-command": "reliability-audit :: reliability.migration-immutable",
    "atomic-write-command": "reliability-audit :: reliability.atomic-write",
    "reproducible-build-command": "release-audit :: release.reproducible-artifact",
    "core-web-vitals-command": "audit-website :: web.core-web-vitals",
    "billing-harness-commands": "commercial-readiness :: sell-01 … sell-06 (a map check -> command)",
}
ASVS = "owasp-asvs-5.0"  # chapter numbers below are ASVS 5.0.0 (OWASP/ASVS tag v5.0.0, 5.0/en)


class Runner:
    def __init__(self, repo: Path, plugin: Path, gates: dict, dry_run=False,
                 website_url="", website_dir=""):
        self.repo, self.plugin, self.gates = repo, plugin, gates
        self.platform = str(gates.get("platform", ""))
        self.hints = gates.get("adapter-hints") or {}
        self.dry = dry_run
        self.website_url, self.website_dir = website_url, website_dir
        self.audit = repo / ".audit"
        self.last_exit = 0
        self.results: dict[str, dict] = {}
        self.head = self._git("rev-parse", "--short", "HEAD")
        self.python = sys.executable or "python3"

    # ------------------------------------------------------------ helpers

    def _git(self, *args) -> str:
        try:
            return subprocess.run(["git", *args], cwd=self.repo, capture_output=True,
                                  text=True, timeout=60).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""  # not a git checkout: the evidence says head is unknown

    def instrument(self, owner: str, rel: str) -> Path:
        d = ve.skill_dir(self.plugin, owner)
        return (d / rel) if d else self.plugin / "missing" / owner / rel

    def cfg(self, owner: str) -> dict:
        """The owner's own settings in gates.json (`owners.<owner>`), under its current or old name."""
        for raw, value in (self.gates.get("owners") or {}).items():
            if ve.canonical_owner(raw) == owner and isinstance(value, dict):
                return value
        return {}

    @staticmethod
    def is_own(path: Path) -> bool:
        """Did an earlier run of this script write the file? Its stamp says so."""
        try:
            return bool(OWN_STAMP.search(path.read_text(encoding="utf-8", errors="replace")))
        except OSError:
            return False

    def clear_own(self, owner: str):
        """A check this run no longer writes must not survive from an earlier run — but only
        this script's own files go. What an owner skill or audit-app's reading wrote by hand,
        and the logs those files cite, are theirs to replace (CONTRACTS §4.1.5)."""
        d = self.audit / owner
        if not d.is_dir():
            return
        kept = [p for p in d.rglob("*.evidence.yaml") if not self.is_own(p)]
        cited = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in kept)
        for p in sorted(d.rglob("*"), reverse=True):  # children before their folder
            if p.is_dir():
                if not any(p.iterdir()):
                    p.rmdir()
            elif p not in kept and p.relative_to(self.repo).as_posix() not in cited:
                p.unlink()
        if not any(d.iterdir()):
            d.rmdir()

    def tally(self, owner: str, result: str):
        r = self.results.setdefault(owner, {"ran": 0, "PASS": 0, "FAIL": 0, "NOT_VERIFIED": 0, "NOT_APPLICABLE": 0})
        r["ran"] += 1
        r[result] = r.get(result, 0) + 1

    def write(self, owner, check, instrument, rule, result, *, producer=None, rule_version="",
              severity="", command="", log="", reason="", evidence=()):
        producer = producer or owner
        target = self.audit / owner / f"{producer}--{check}.evidence.yaml"
        if result == "NOT_VERIFIED" and target.is_file() and not self.is_own(target):
            # A gap this script cannot fill never replaces what the owner settled by hand.
            print(f"       [keep] {owner}::{check} — settled in {target.name}; the runner has no instrument for it")
            return
        if result == "PASS" and (not command or not log):
            raise RuntimeError(f"refusing to write PASS for {owner}::{check} without command+log (CONTRACTS §4.6)")
        if result == "PASS" and not (self.repo / log).is_file():
            raise RuntimeError(f"refusing to write PASS for {owner}::{check} — log not on disk: {log}")
        self.tally(owner, result)
        if self.dry:
            print(f"       [dry-run] would write {owner}::{check} = {result}")
            return
        conf = "OBSERVED" if command and log else ("INFERRED" if result == "FAIL" else "UNKNOWN")
        q = lambda s: '"' + str(s).replace("\\", "/").replace('"', "'").replace("\n", " ")[:200] + '"'  # noqa: E731
        out = [f"check: {check}", f"owner: {owner}", f"producer: {producer}", f"instrument: {instrument}",
               f"rule: {rule}"]
        if rule_version:
            out.append(f"rule-version: {q(rule_version)}")
        out += ["methods:", f"  - {instrument}"]
        items = list(evidence) or ([log] if log else [])
        if items:
            out.append("evidence:")
            for e in items:
                out += [f"  - path: {q(e)}", "    kind: command-output"]
        else:
            out.append("evidence: []")
        out.append(f"result: {result}")
        if severity:
            out.append(f"severity: {severity}")
        out.append(f"confidence: {conf}")
        if command:
            out.append(f"command: {q(command)}")
        if log:
            out.append(f"log: {log}")
        if reason:
            out.append("reason: |")
            out += [f"  {line}" for line in str(reason).splitlines()]
        out += ["context:", f"  head: {self.head or 'unknown'}", f"  platform: {self.platform}",
                f"  captured-at: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
                f"  producer-script: {PRODUCER_SCRIPT}"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(out) + "\n", encoding="utf-8")

    def missing(self, owner, instrument, why):
        self.write(owner, f"{owner}.instrument-available", instrument, "instrument-present",
                   "NOT_VERIFIED", reason=f"missing-instrument: {why}")

    def logged(self, cmd: str, log_rel: str) -> bool | None:
        """Run a shell command in the repo root, output to log_rel. None in dry-run."""
        if self.dry:
            print(f"       [dry-run] {cmd}  -> {log_rel}")
            return None
        log = self.repo / log_rel
        log.parent.mkdir(parents=True, exist_ok=True)
        try:
            p = subprocess.run(cmd, shell=True, cwd=self.repo, capture_output=True, text=True,
                               timeout=TIMEOUT, encoding="utf-8", errors="replace")
            log.write_text((p.stdout or "") + (p.stderr or ""), encoding="utf-8")
            self.last_exit = p.returncode
            return p.returncode == 0
        except subprocess.TimeoutExpired:
            log.write_text(f"[runner] timeout after {TIMEOUT}s\n", encoding="utf-8")
            self.last_exit = 124
            return False

    def json_instrument(self, owner, script: Path, instrument, *, producer=None, check_override="",
                        only_results=(), skip_checks=(), rule="declared-by-owner", rule_version="", extra=()):
        """A Python instrument that prints {results:[{check,result,severity,reason,evidence}]}.
        Its stdout is the log, so every PASS carries command + log. `skip_checks` are the
        checks another instrument of this run settles."""
        if not script.is_file():
            self.missing(owner, instrument, f"instrument not found at {script}")
            return
        log_rel = f".audit/{owner}/{instrument}.log"
        json_rel = f".audit/{owner}/{instrument}.json"
        argv = [self.python, str(script), "--repo", str(self.repo), *extra]
        cmd = " ".join(f'"{a}"' if " " in a else a for a in argv)
        if self.dry:
            print(f"       [dry-run] {cmd}")
            return
        (self.audit / owner).mkdir(parents=True, exist_ok=True)
        try:
            p = subprocess.run(argv, cwd=self.repo, capture_output=True, text=True, timeout=TIMEOUT,
                               encoding="utf-8", errors="replace")
            stdout, stderr = p.stdout, p.stderr
        except subprocess.TimeoutExpired:
            stdout, stderr = "", f"[runner] timeout after {TIMEOUT}s"
        (self.repo / log_rel).write_text(stderr or "", encoding="utf-8")
        if not stdout.strip():
            self.missing(owner, instrument, f"instrument produced no output (see {log_rel})")
            return
        (self.repo / json_rel).write_text(stdout, encoding="utf-8")
        try:
            report = json.loads(stdout)
        except json.JSONDecodeError:
            self.missing(owner, instrument, f"instrument output is not valid JSON (see {json_rel})")
            return
        for r in report.get("results", []):
            res = str(r.get("result", ""))
            if only_results and res not in only_results or str(r.get("check")) in skip_checks:
                continue
            # What the instrument observed carries its trace; "does not apply" is observed too (§4.3.4).
            traced = res in ("PASS", "FAIL", "NOT_APPLICABLE")
            self.write(owner, check_override or str(r.get("check")), instrument, rule, res,
                       producer=producer, rule_version=rule_version, severity=str(r.get("severity") or ""),
                       command=cmd if traced else "", log=json_rel if traced else "",
                       reason=str(r.get("reason") or ""), evidence=[str(e) for e in r.get("evidence") or []])

    def declared(self, owner, check, instrument, rule, key, *, fail_severity="BLOCKER", rule_version=""):
        """A command the project declares in adapter-hints: exit 0 PASS, != 0 FAIL, none = gap said."""
        cmd = str(self.hints.get(key, "") or "")
        if not cmd:
            self.write(owner, check, instrument, rule, "NOT_VERIFIED", rule_version=rule_version,
                       reason=f"adapter-hints.{key} not declared in gates.json")
            return
        log_rel = f".audit/{owner}/{check}.log"
        ok = self.logged(cmd, log_rel)
        if ok is None:
            self.tally(owner, "NOT_VERIFIED")
            return
        if ok:
            self.write(owner, check, instrument, rule, "PASS", rule_version=rule_version, command=cmd, log=log_rel)
        elif self.last_exit == CANNOT_RUN:
            self.write(owner, check, instrument, rule, "NOT_VERIFIED", rule_version=rule_version,
                       reason=f"cannot-run-here: `{cmd}` exited {CANNOT_RUN}, its way of saying what it needs "
                              f"is missing; see {log_rel}")
        elif unprepared(self.repo):
            self.write(owner, check, instrument, rule, "NOT_VERIFIED", rule_version=rule_version,
                       reason=f"cannot-run-here: {unprepared(self.repo)} (`{cmd}` exited {self.last_exit}; "
                              f"see {log_rel})")
        else:
            self.write(owner, check, instrument, rule, "FAIL", rule_version=rule_version,
                       severity=fail_severity, command=cmd, log=log_rel)

    # ------------------------------------------------------------ owners

    def code_audit(self):
        o = "code-audit"
        for check, key, inst, rule in (("runtime.build-passes", "build-command", "build-runner", "release-clean"),
                                       ("runtime.types-check", "typecheck-command", "build-runner", "typecheck-clean"),
                                       ("runtime.tests-pass", "tests-command", "test-runner", "suite-green")):
            self.declared(o, check, inst, rule, key)
        for c in ("runtime.tests-have-oracles", "runtime.concurrency-safe", "runtime.no-silent-panics",
                  "runtime.cancellation-cleaned", "contract.timeout-declared", "contract.retry-idempotent",
                  "contract.schema-compat", "contract.failure-modes-declared", "contract.input-not-trusted",
                  "contract.side-effects-bounded", "contract.cancellation-honoured", "contract.layer-direction",
                  "perf.budgets-declared", "perf.bundle-within-budget", "perf.hot-path-met", "perf.no-regressions"):
            self.write(o, c, "static-analysis", "declared-by-owner", "NOT_VERIFIED",
                       reason="missing-instrument: needs the code-audit owner to review against the diff and "
                              "cite the test that proves it; this runner only executes build/typecheck/tests.")
        self.json_instrument(o, self.instrument(o, "scripts/quality_scan.py"), "quality-scan",
                             rule="maintainability-budgets")
        if self.platform in ("web", "both"):
            self.json_instrument(o, self.instrument(o, "scripts/webhook_idempotency.py"), "webhook-idempotency",
                                 rule="inbound-contract-idempotency", rule_version="contract-4.6",
                                 extra=["--platform", self.platform])

    def ui_system(self):
        o = "ui-system"
        script = self.instrument(o, "scripts/audit_ui.py")
        cfg = self.repo / "ui.config.json"
        if not script.is_file():
            return self.missing(o, "audit_ui.py", f"audit_ui.py not found (install pqr-ui-system): {script}")
        if not cfg.is_file():
            return self.missing(o, "audit_ui.py", "ui.config.json not present at repo root — instrument has no target")
        json_rel, md_rel, log_rel = (f".audit/{o}/audit_ui.json", f".audit/{o}/audit_ui.md", f".audit/{o}/audit_ui.log")
        cmd = (f'"{self.python}" "{script}" --repo "{self.repo}" --config "{cfg}" '
               f'--json-output "{self.repo / json_rel}" --markdown-output "{self.repo / md_rel}"')
        for d in ((self.gates.get("owners") or {}).get(o) or {}).get("ignore-dirs", []) or []:
            cmd += f' --ignore-dir "{d}"'
        ok = self.logged(cmd, log_rel)
        if ok is None:
            return
        if not (self.repo / json_rel).is_file():
            return self.missing(o, "audit_ui.py", f"audit_ui.py produced no JSON (see {log_rel})")
        report = json.loads((self.repo / json_rel).read_text(encoding="utf-8"))
        kinds_by_check = {
            "ui.architectural-boundary": ["external-ui-import"], "ui.legacy-package": ["legacy-ui-alias"],
            "ui.invalid-boolean-selector": ["boolean-state-selector"], "ui.color-mix-sum": ["color-mix-sum"],
            "ui.oklch-delta-l": ["oklch-contrast-low", "raw-hex", "raw-color-function", "arbitrary-color-utility"],
            "ui.remote-fonts": ["remote-resource"], "ui.ai-generic-fonts": ["generic-font"],
            "ui.focus-ring": ["focus-box-shadow"], "ui.reduced-motion": ["missing-reduced-motion"],
            "ui.unstyled-component": ["unstyled-component"]}
        for check, kinds in kinds_by_check.items():
            errs = [f for f in report.get("findings", []) if f.get("kind") in kinds and f.get("severity") == "error"]
            if errs:
                lines = [f"{f.get('file')}:{f.get('line')} [{f.get('kind')}] {f.get('value')}" for f in errs[:5]]
                self.write(o, check, "audit_ui.py", "data-ui-contract", "FAIL", severity="HIGH", command=cmd,
                           log=log_rel, evidence=lines,
                           reason=f"{len(errs)} error finding(s) of kind {kinds}; full list in {md_rel}")
            else:
                self.write(o, check, "audit_ui.py", "data-ui-contract", "PASS", command=cmd, log=log_rel,
                           evidence=[json_rel],
                           reason=f"0 error findings of kind {kinds} across {report.get('files_scanned')} files")

    def audit_website(self):
        o = "audit-website"
        node = shutil.which("node")
        engine = self.instrument(o, "scripts/run_website_audit.mjs")
        seo = self.instrument(o, "seo/run_seo_audit.mjs")
        if not node:
            return self.missing(o, "run_website_audit.mjs", "node not on PATH")
        if not engine.is_file():
            return self.missing(o, "run_website_audit.mjs", f"engine not found (install pqr-website): {engine}")
        declared = str(self.cfg(o).get("target") or "")  # gates.json: a URL, or a built folder
        url = self.website_url or (declared if declared.startswith(("http://", "https://")) else "")
        folder = self.website_dir or ("" if url else declared)
        target = f"--url={url}" if url else (f"--dir={folder}" if folder else "")
        if not target:
            return self.missing(o, "run_website_audit.mjs",
                                "no target: declare owners.audit-website.target in gates.json, or pass "
                                "--website-url / --website-dir")
        for name, path, check in (("run_website_audit.mjs", engine, "web.readiness-clean"),
                                  ("run_seo_audit.mjs", seo, "web.seo-technical")):
            if not path.is_file():
                self.tally(o, "NOT_VERIFIED")
                continue
            log_rel = f".audit/{o}/{name}.log"
            cmd = f'node "{path}" {target}' + (f' --out-dir="{self.audit / o}"' if name == "run_seo_audit.mjs" else "")
            ok = self.logged(cmd, log_rel)
            if ok is None:
                continue
            if ok:
                self.write(o, check, name, "sarif-2.1.0", "PASS", rule_version="sarif-2.1.0", command=cmd, log=log_rel)
            else:
                self.write(o, check, name, "sarif-2.1.0", "FAIL", rule_version="sarif-2.1.0", severity="HIGH",
                           command=cmd, log=log_rel, reason="engine exited non-zero; see log and SARIF")
        # Core Web Vitals need a browser on the real pages (or field data behind a key): the
        # project's own measurement settles the check, or the gap is said.
        self.declared(o, "web.core-web-vitals", "measurement-run", "cwv-within-thresholds",
                      "core-web-vitals-command", fail_severity="HIGH")

    def security_audit(self):
        o = "security-audit"
        dep_cmd = ""
        if (self.repo / "package-lock.json").is_file():
            dep_cmd = "npm audit --audit-level=high"
        elif (self.repo / "pnpm-lock.yaml").is_file() and shutil.which("pnpm"):
            dep_cmd = "pnpm audit --audit-level high"
        elif (self.repo / "yarn.lock").is_file() and shutil.which("yarn"):
            dep_cmd = "yarn npm audit --severity high"
        elif (self.repo / "Cargo.lock").is_file() and shutil.which("cargo-audit"):
            dep_cmd = "cargo audit"
        rule = f"{ASVS} V15.2"  # Security Architecture and Dependencies
        if dep_cmd:
            log_rel = f".audit/{o}/sec.deps-no-cve.log"
            ok = self.logged(dep_cmd, log_rel)
            if ok is True:
                self.write(o, "sec.deps-no-cve", "dep-scanner", rule, "PASS", rule_version=ASVS,
                           command=dep_cmd, log=log_rel)
            elif ok is False:
                self.write(o, "sec.deps-no-cve", "dep-scanner", rule, "FAIL", rule_version=ASVS,
                           severity="HIGH", command=dep_cmd, log=log_rel)
        else:
            self.write(o, "sec.deps-no-cve", "dep-scanner", rule, "NOT_VERIFIED", rule_version=ASVS,
                       reason="missing-instrument: no lockfile-based scanner available (npm/pnpm/yarn/cargo audit)")
        self.json_instrument(o, self.instrument(o, "scripts/tenant_isolation.py"), "tenant-isolation",
                             rule=f"{ASVS} V8.2", rule_version=ASVS, extra=["--platform", self.platform])
        gl = self.audit / "gitleaks-report.json"
        self.json_instrument(o, self.instrument(o, "scripts/secret_scan.py"), "secret-scanner",
                             rule=f"{ASVS} V13.3", rule_version=ASVS,
                             extra=["--gitleaks-report", str(gl)] if gl.is_file() else [])
        doc = str(self.cfg(o).get("threat-model") or "")
        self.json_instrument(o, self.instrument(o, "scripts/threat_model.py"), "threat-model-check",
                             rule=f"{ASVS} V15.1", rule_version=ASVS, extra=["--doc", doc] if doc else [])

    def release_audit(self):
        o = "release-audit"
        lock = next((f for f in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "Cargo.lock")
                     if (self.repo / f).is_file()), None)
        if lock:
            cmd = f"git ls-files --error-unmatch {lock}"
            log_rel = f".audit/{o}/release.lockfiles-immutable.log"
            ok = self.logged(cmd, log_rel)
            if ok is True:
                self.write(o, "release.lockfiles-immutable", "reproducibility-run", "lockfile-committed", "PASS",
                           command=cmd, log=log_rel, evidence=[lock],
                           reason="lockfile tracked by git; CI must install frozen (checked by ci-inspection)")
            elif ok is False:
                self.write(o, "release.lockfiles-immutable", "reproducibility-run", "lockfile-committed", "FAIL",
                           severity="HIGH", command=cmd, log=log_rel)
        elif any((self.repo / f).is_file() for f in ("package.json", "Cargo.toml")):
            self.write(o, "release.lockfiles-immutable", "reproducibility-run", "lockfile-committed", "FAIL",
                       severity="HIGH", reason="no lockfile found beside package.json / Cargo.toml")
        else:
            self.write(o, "release.lockfiles-immutable", "reproducibility-run", "lockfile-committed", "NOT_VERIFIED",
                       reason="missing-instrument: this runner knows npm, pnpm, yarn and Cargo lockfiles, and the "
                              "repo root has neither package.json nor Cargo.toml")
        sbom = self.repo / "sbom.json"
        if not sbom.is_file():
            self.write(o, "release.sbom-present", "sbom-verifier", "cyclonedx-synced", "FAIL", severity="MEDIUM",
                       reason="sbom.json not found at repo root")
        elif shutil.which("node") and (self.repo / "package.json").is_file():
            cmd = ('node -e "const s=require(\'./sbom.json\');const p=require(\'./package.json\');'
                   'if((s.metadata||{}).component&&s.metadata.component.version!==p.version){'
                   'console.error(\'SBOM \'+s.metadata.component.version+\' != package \'+p.version);process.exit(1)}'
                   'console.log(\'sbom ok \'+p.version)"')
            log_rel = f".audit/{o}/release.sbom-present.log"
            ok = self.logged(cmd, log_rel)
            if ok is True:
                self.write(o, "release.sbom-present", "sbom-verifier", "cyclonedx-synced", "PASS", command=cmd,
                           log=log_rel, evidence=["sbom.json"])
            elif ok is False:
                self.write(o, "release.sbom-present", "sbom-verifier", "cyclonedx-synced", "FAIL", severity="MEDIUM",
                           command=cmd, log=log_rel)
        else:
            self.write(o, "release.sbom-present", "sbom-verifier", "cyclonedx-synced", "NOT_VERIFIED",
                       reason="sbom.json exists but no node/package.json to verify version sync")
        own_repro = bool(self.hints.get("reproducible-build-command"))
        mdir = str(self.cfg("reliability-audit").get("migrations-dir") or "")
        self.json_instrument(o, self.instrument(o, "scripts/ci_inspection.py"), "ci-inspection",
                             rule="clean-clone-one-command",
                             extra=["--platform", self.platform, *(["--migrations", mdir] if mdir else [])],
                             skip_checks=("release.reproducible-artifact",) if own_repro else ())
        if own_repro:  # two clean builds and a hash compare are the project's to run
            self.declared(o, "release.reproducible-artifact", "reproducibility-run", "same-commit-same-artifact",
                          "reproducible-build-command", fail_severity="HIGH")
        if self.platform != "web":
            for c in ("release.signed-artifact", "release.updater-verified"):
                self.write(o, c, "signature-verifier", "declared-by-owner", "NOT_VERIFIED",
                           reason="missing-instrument: needs the signed installer/updater manifest and a verification run")

    def reliability_audit(self):
        o = "reliability-audit"
        harness = self.instrument(o, "scripts/migration_harness.py")
        mdir = str(self.cfg(o).get("migrations-dir") or "")
        # One check, one settler: where the project declares its own verifier, that command
        # decides migration-immutable and the harness's reading of the same check is dropped.
        own_verifier = bool(self.hints.get("migrations-verify-command"))
        self.json_instrument(o, harness, "migration-harness", rule="no-data-loss",
                             extra=["--migrations", mdir] if mdir else [],
                             skip_checks=("reliability.migration-immutable",) if own_verifier else ())
        if own_verifier:
            self.declared(o, "reliability.migration-immutable", "migration-harness",
                          "published-migrations-unchanged", "migrations-verify-command")
        # Where the code that runs in production lives: a CLI script's output is not a log.
        src = [x for d in self.cfg(o).get("source-dirs") or [] for x in ("--src", str(d))]
        self.json_instrument(o, self.instrument(o, "scripts/log_inspection.py"), "log-inspection",
                             rule="diagnosable-in-production", extra=["--platform", self.platform, *src])
        gaps = ["reliability.resume-after-reopen"]
        if self.hints.get("atomic-write-command"):  # the project's own kill-mid-write harness
            self.declared(o, "reliability.atomic-write", "crash-harness", "write-is-all-or-nothing",
                          "atomic-write-command")
        else:
            gaps.insert(0, "reliability.atomic-write")
        if self.platform != "web":
            gaps += ["reliability.crash-mid-write", "reliability.no-double-flush"]
        for c in gaps:
            inst = "crash-harness" if ("crash" in c or "flush" in c) else "migration-harness"
            self.write(o, c, inst, "declared-by-owner", "NOT_VERIFIED",
                       reason=f"missing-instrument: requires a project-local {inst} that kills the process "
                              "mid-write (or races two concurrent writers) and reopens")

    def _declared_command(self, owner, instrument, rule, rule_version, hint, checks):
        self.json_instrument(owner, HERE / "declared-command.py", instrument, rule=rule, rule_version=rule_version,
                             extra=["--owner", owner, "--hint", hint, "--checks", checks])

    def design_pro(self):
        self._declared_command("design-pro", "adapter-local", "a11y-critical-flows", "wcag-2.2-AA",
                               "design-pro-capture-command", "a11y-critical-flows")

    def verify(self):
        self._declared_command("verify", "adapter-local", "smoke-against-the-real-environment", "contract-4.6",
                               "smoke-command", "smoke-test-passes")

    def commercial_readiness(self):
        o = "commercial-readiness"
        self._declared_command(o, "billing-harness", "sell-paths", "contract-4.6", "billing-harness-commands",
                               "sell-01-activation,sell-02-offline-or-failure,sell-03-machine-or-account-change,"
                               "sell-04-trial-to-paid,sell-05-refund-cancel,sell-06-end-of-payment")
        # sell-01, the static half: the webhook reading can FAIL sell-01, never PASS it.
        if self.platform in ("web", "both"):
            self.json_instrument(o, self.instrument("code-audit", "scripts/webhook_idempotency.py"),
                                 "webhook-idempotency", producer="code-audit", check_override="sell-01-activation",
                                 only_results=("FAIL",), rule="inbound-contract-idempotency",
                                 rule_version="contract-4.6", extra=["--platform", self.platform])

    def drive_app_window(self):
        self.missing("drive-app-window", "gui.ps1",
                     "requires a project-local gui.ps1 the plugin cannot ship (see pqr-desktop/drive-app-window)")

    DISPATCH = {"code-audit": code_audit, "ui-system": ui_system, "audit-website": audit_website,
                "security-audit": security_audit, "release-audit": release_audit,
                "reliability-audit": reliability_audit, "design-pro": design_pro, "verify": verify,
                "commercial-readiness": commercial_readiness, "drive-app-window": drive_app_window}


def owner_platforms(plugin: Path, owner: str) -> list[str]:
    m = ve.load_manifest(plugin, owner) or {}
    p = m.get("platforms")
    return p if isinstance(p, list) and p else ["web", "desktop"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--plugin", default=None, help="plugin root (default: this marketplace or plugin)")
    ap.add_argument("--only", default="", help="comma-separated owners")
    ap.add_argument("--skip", default="", help="comma-separated owners")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--website-url", default="")
    ap.add_argument("--website-dir", default="")
    ap.add_argument("--no-gates", action="store_true", help="write evidence only; do not apply the gates")
    ap.add_argument("--list-hints", action="store_true", help="print the adapter-hints this runner reads, and exit")
    a = ap.parse_args(argv)
    if a.list_hints:
        for key, settles in HINTS.items():
            print(f"{key:28} {settles}")
        return 0
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # an old interpreter keeps its encoding; output is still ASCII-safe enough
        pass

    repo = Path(a.repo).resolve()
    plugin = Path(a.plugin).resolve() if a.plugin else ve.find_plugin(repo, None)
    if plugin is None:
        print("plugin root not found (pass --plugin)", file=sys.stderr)
        return 2
    gates, gates_path = ve.load_gates(repo)
    if not gates or not gates.get("owners"):
        print("gates.json missing or without 'owners' (.agents/ or .claude/). Run bootstrap-project first.",
              file=sys.stderr)
        return 2
    platform = str(gates.get("platform", ""))
    if platform not in ("web", "desktop", "both"):
        print("gates.json has no 'platform' (web | desktop | both). Required by CONTRACTS §5.4.", file=sys.stderr)
        return 2
    only = {ve.canonical_owner(x.strip()) for x in a.only.split(",") if x.strip()}
    skip = {ve.canonical_owner(x.strip()) for x in a.skip.split(",") if x.strip()}
    print(f"run_all_owners\n  repo:     {repo}\n  plugin:   {plugin}\n  gates:    {gates_path}\n  platform: {platform}\n")

    r = Runner(repo, plugin, gates, a.dry_run, a.website_url, a.website_dir)
    unread = sorted(k for k in r.hints if k not in HINTS)
    if unread:
        print(f"  [note] adapter-hints this runner does not read (--list-hints shows the ones it does): "
              f"{', '.join(unread)}\n")
    for raw, cfg in gates["owners"].items():
        name = ve.canonical_owner(raw)
        if isinstance(cfg, dict) and cfg.get("not-applicable"):
            print(f"  [skip] {name} — not-applicable: {cfg['not-applicable']}")
            continue
        if name not in Runner.DISPATCH:
            continue  # the cycle adapters and audit-app have nothing to run
        if only and name not in only or name in skip:
            continue
        plats = owner_platforms(plugin, name)
        if platform != "both" and platform not in plats:
            print(f"  [skip] {name} — platforms {plats} do not include '{platform}'")
            continue
        print(f"  [->] {name}")
        if not a.dry_run:
            r.clear_own(name)
        try:
            Runner.DISPATCH[name](r)
        except Exception as e:  # one owner's crash is reported and the others still run
            print(f"  [x]  {name} threw: {e}", file=sys.stderr)

    if r.head and r._git("rev-parse", "--short", "HEAD") != r.head:
        print("WARNING: HEAD moved during the run.")
    print("\nPer-owner summary:")
    print(f"  {'owner':22} {'ran':>4} {'pass':>5} {'fail':>5} {'not_verified':>13}")
    for k in sorted(r.results):
        x = r.results[k]
        print(f"  {k:22} {x['ran']:>4} {x['PASS']:>5} {x['FAIL']:>5} {x['NOT_VERIFIED']:>13}")
    if a.dry_run or a.no_gates:
        return 0
    print()
    import apply_gates  # noqa: E402 — after the evidence exists
    return apply_gates.main(["--repo", str(repo), "--plugin", str(plugin)])


if __name__ == "__main__":
    sys.exit(main())
