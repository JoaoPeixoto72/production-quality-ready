#!/usr/bin/env python3
"""Each instrument's red case — the rule that makes a gate worth something.

An instrument never seen red is not a gate: nobody knows it detects what it
claims. Each class builds a **bad** repository and asserts the instrument
catches it. `EveryInstrumentHasARedCase` enforces itself: it reads every skill's
`instruments.yaml` and fails on an instrument that is neither here nor excused.

    python -m unittest discover -s tests/instruments -p "test_*.py"
"""

from __future__ import annotations

import contextlib
import http.server
import json
import re
import subprocess
import threading
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------- registo

# instrument -> (script implementing it, class proving it goes red)
RED_CASE: dict[str, tuple[str, str]] = {
    "quality-scan": ("skills/code-review/scripts/quality_scan.py", "QualityScanGoesRed"),
    "audit_ui.py": ("skills/ui-system/scripts/audit_ui.py", "AuditUiGoesRed"),
    "secret-scanner": ("skills/security-audit/scripts/secret_scan.py", "SecretScanGoesRed"),
    "migration-harness": ("skills/reliability-audit/scripts/migration_harness.py", "MigrationHarnessGoesRed"),
    "log-inspection": ("skills/reliability-audit/scripts/log_inspection.py", "LogInspectionGoesRed"),
    "ci-inspection": ("skills/release-audit/scripts/ci_inspection.py", "CiInspectionGoesRed"),
    "threat-model-check": ("skills/security-audit/scripts/threat_model.py", "ThreatModelGoesRed"),
    "tenant-isolation": ("skills/security-audit/scripts/tenant_isolation.py", "TenantIsolationGoesRed"),
    "adapter-local": ("scripts/declared-command.py", "DeclaredCommandGoesRed"),
    "trim-check": ("skills/close-work/scripts/trim_check.py", "TrimCheckGoesRed"),
    "billing-harness": ("scripts/declared-command.py", "DeclaredCommandGoesRed"),
    "run_seo_audit.mjs": ("skills/audit-website/seo/run_seo_audit.mjs", "SeoEngineGoesRed"),
    "run_website_audit.mjs": ("skills/audit-website/scripts/run_website_audit.mjs", "WebsiteEngineGoesRed"),
}

# Instruments that are not ours to test, each with its reason (an exception without one is no rule).
NO_RED_CASE: dict[str, str] = {
    "dep-scanner": "external command (`npm audit`), not our code",
    "test-runner": "runs the project's suite; red is the project itself failing",
    "build-runner": "runs the project's build; same",
    "measurement-run": "runs the project's measurement harness; same",
    "static-analysis": "analysis by the agent reading code, not an instrument",
    "reproducibility-run": "two project builds compared by the runner",
    "clean-run": "a clean clone of the project made by the runner",
    "crash-harness": "crash harness written in the project (project-local)",
    "dom-inspection": "DOM inspection in the project's browser",
    "keyboard-traversal": "keyboard traversal in the project's browser",
    "screenshot-sample": "project captures, in an INTERACTIVE environment",
    "licensing-harness": "licensing harness written in the project",
    "legal-inspection": "reading the project's legal documents",
    "sbom-verifier": "`sbom.json` check written inline in the runner",
    "signature-verifier": "artefact signature check, in the project",
    "browser-driver": "the host's browser driver (chrome-devtools/Playwright)",
    "gui.ps1": "the project's window driver",
    "deploy-smoke": "the smoke runs against the real environment; red is the deploy failing",
    "release-run": "the release is run by the `ship` owner, not by a script of ours",
    "npm-audit": "external command",
}


# --------------------------------------------------------------- helpers

def run(cmd: list[str], cwd: Path, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def instrument_json(script: str, args: list[str], cwd: Path) -> tuple[int, dict]:
    """Run a Python instrument and return (exit, stdout JSON)."""
    p = run([sys.executable, str(PLUGIN / script), *args], cwd)
    try:
        return p.returncode, json.loads(p.stdout)
    except json.JSONDecodeError:
        raise AssertionError(f"instrument returned no JSON: {script}\n"
                             f"exit={p.returncode}\nstdout={p.stdout[:400]}\nstderr={p.stderr[:400]}")


def by_check(payload: dict) -> dict[str, dict]:
    return {r["check"]: r for r in payload["results"]}


def node_run(script: str, args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    p = run(["node", str(PLUGIN / script), *args], cwd or PLUGIN)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


# --------------------------------------------------------------- servidor local

@contextlib.contextmanager
def local_site(files: dict[str, str]):
    """Serve `files` on 127.0.0.1 and return (url, root); `{url}` in contents becomes the real address.
    The engines must be exercised over the network, not only with `--dir`."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        root.mkdir(parents=True, exist_ok=True)

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *a, **kw):
                super().__init__(*a, directory=str(root), **kw)

            def log_message(self, *a):
                pass

        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        url = f"http://127.0.0.1:{srv.server_address[1]}"
        for name, text in files.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text.replace("{url}", url), encoding="utf-8")
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            yield url, root
        finally:
            srv.shutdown()


# --------------------------------------------------------------- the cases

class QualityScanGoesRed(unittest.TestCase):
    def test_a_file_over_the_budget_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "big.ts").write_text(
                "\n".join(f"export const x{i} = {i}" for i in range(1100)), encoding="utf-8")
            code, payload = instrument_json(
                "skills/code-review/scripts/quality_scan.py", ["--repo", ".", "--format", "json"], root)
            self.assertNotEqual(code, 0, "an exceeded budget must exit != 0")
            self.assertEqual(by_check(payload)["quality.file-size"]["result"], "FAIL")


class AuditUiGoesRed(unittest.TestCase):
    def test_raw_hex_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "public").mkdir()
            (root / "public" / "style.css").write_text(".a { color: #ff0000; }\n", encoding="utf-8")
            p = run([sys.executable, str(PLUGIN / "skills/ui-system/scripts/audit_ui.py"),
                     "--repo", ".", "--json-output", "ui.json"], root)
            report = json.loads((root / "ui.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(report["error_count"], 1)
            self.assertEqual(report["summary"].get("raw-hex"), 1)
            self.assertTrue(any(f["kind"] == "raw-hex" for f in report["findings"]))
            self.assertEqual(p.returncode, 0, "without --strict the instrument reports without failing the process")


class SecretScanGoesRed(unittest.TestCase):
    def test_a_key_in_a_plain_text_file_fails(self):
        """A private key in a plain-text notes file is not a fixture."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "notes.txt").write_text(
                "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEAx7f9\n-----END RSA PRIVATE KEY-----\n",
                encoding="utf-8")
            dummy_key = "AKIA" + "3XQ7ZP2LMNVB4RTY"
            (root / "app.js").write_text(f"const k = '{dummy_key}'\n", encoding="utf-8")
            run(["git", "init", "-q"], root)
            run(["git", "add", "-A"], root)
            run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "x"], root)
            _, payload = instrument_json(
                "skills/security-audit/scripts/secret_scan.py", ["--repo", ".", "--no-history"], root)
            r = by_check(payload)["sec.secrets-not-committed"]
            self.assertEqual(r["result"], "FAIL")
            self.assertEqual(r["severity"], "BLOCKER")
            self.assertTrue(any("private-key-block" in e for e in r["evidence"]))

    def test_an_empty_scan_never_passes(self):
        """Without git nothing is read; a PASS would say 'no secrets' without looking."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "notes.txt").write_text("nada\n", encoding="utf-8")
            _, payload = instrument_json(
                "skills/security-audit/scripts/secret_scan.py", ["--repo", ".", "--no-history"], root)
            r = by_check(payload)["sec.secrets-not-committed"]
            self.assertEqual(r["result"], "NOT_VERIFIED")
            self.assertIn("nothing was scanned", r["reason"])


class MigrationHarnessGoesRed(unittest.TestCase):
    def test_a_broken_migration_fails_the_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "migrations").mkdir()
            (root / "migrations" / "0001_broken.sql").write_text("CREATE TABL oops (id INTEGER);\n",
                                                                 encoding="utf-8")
            _, payload = instrument_json(
                "skills/reliability-audit/scripts/migration_harness.py", ["--repo", "."], root)
            r = by_check(payload)["reliability.migration-forward"]
            self.assertEqual(r["result"], "FAIL")
            self.assertEqual(r["severity"], "BLOCKER")


class LogInspectionGoesRed(unittest.TestCase):
    def test_no_correlation_id_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "app.ts").write_text(
                "export function handler() { console.log('hello') }\n", encoding="utf-8")
            _, payload = instrument_json(
                "skills/reliability-audit/scripts/log_inspection.py",
                ["--repo", ".", "--platform", "web"], root)
            checks = by_check(payload)
            self.assertEqual(checks["observability.correlation-id-e2e"]["result"], "FAIL")
            self.assertEqual(checks["observability.logs-structured"]["result"], "FAIL")


class CiInspectionGoesRed(unittest.TestCase):
    def test_no_rollback_declared_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / ".github" / "workflows" / "ci.yml").write_text(
                "name: ci\non: [push]\njobs:\n  build:\n    steps:\n      - run: echo hi\n",
                encoding="utf-8")
            _, payload = instrument_json(
                "skills/release-audit/scripts/ci_inspection.py",
                ["--repo", ".", "--platform", "web"], root)
            checks = by_check(payload)
            self.assertEqual(checks["release.rollback-declared"]["result"], "FAIL")
            self.assertEqual(checks["release.deploy-single-command"]["result"], "FAIL")


class SeoEngineGoesRed(unittest.TestCase):
    def test_a_page_without_title_fails_the_build_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text("<html><body><h1>no head</h1></body></html>", encoding="utf-8")
            code, out = node_run("skills/audit-website/seo/run_seo_audit.mjs", [f"--dir={root}"])
            self.assertIn("BUILD-TITLE-01", out)
            self.assertIn("[FAIL]", out)
            self.assertIn("FIX_BEFORE_LAUNCH", out)
            self.assertNotEqual(code, 0)


class EnginesSurviveANetworkTarget(unittest.TestCase):
    """Against a local `http://` target the engines must exit with a code, not abort
    (libuv `UV_HANDLE_CLOSING`, exit 0xC0000409)."""

    ABORT = 0xC0000409

    def test_seo_engine_against_a_local_server(self):
        with local_site({
            "index.html": "<html><head><title>Um titulo local suficientemente longo</title>"
                          "<meta name=\"description\" content=\"A local description long enough to pass "
                          "the minimum of seventy characters the engine requires of it.\">"
                          "<link rel=\"canonical\" href=\"/\"></head><body><h1>Ok</h1></body></html>",
            "robots.txt": "User-agent: *\nAllow: /\nSitemap: {url}/sitemap.xml\n",
            "sitemap.xml": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
                           "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
                           "  <url><loc>{url}/</loc></url>\n"
                           "  <url><loc>{url}/missing.html</loc></url>\n</urlset>\n",
        }) as (url, _):
            code, out = node_run("skills/audit-website/seo/run_seo_audit.mjs", [f"--url={url}"])
            self.assertIn("CRAWL-SITEMAP-STATUS-01", out)
            self.assertIn("[FAIL]", out)
            self.assertNotEqual(code & 0xFFFFFFFF, self.ABORT,
                                "the engine aborted instead of exiting with a code")
            self.assertIn(code, (0, 1), f"exit inesperado: {code}")

    def test_360_engine_against_a_local_server(self):
        with local_site({
            "index.html": "<html><head><title>Um titulo local suficientemente longo</title></head>"
                          "<body><h1>Ok</h1></body></html>",
            "robots.txt": "User-agent: *\nAllow: /\n",
        }) as (url, _):
            code, out = node_run("skills/audit-website/scripts/run_website_audit.mjs",
                                 [f"--url={url}", "--spider-max=1"])
            self.assertIn("Verdict", out, "the report was not printed")
            self.assertNotEqual(code & 0xFFFFFFFF, self.ABORT,
                                "the engine aborted instead of exiting with a code")
            self.assertIn(code, (0, 1, 2), f"exit inesperado: {code}")


class WebsiteEngineGoesRed(unittest.TestCase):
    def test_a_page_without_title_blocks_the_360_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text("<html><body><h1>no head</h1></body></html>", encoding="utf-8")
            _, out = node_run("skills/audit-website/scripts/run_website_audit.mjs", [f"--dir={root}"])
            self.assertIn("BLOCKED", out)
            self.assertIn("CRITICAL", out)


class DeclaredCommandGoesRed(unittest.TestCase):
    """The generic instrument: the command is the project's, the translation ours. An obligation
    without a declared command is `NOT_VERIFIED`, never a PASS inherited from its neighbours."""

    def _repo(self, root: Path, hints: dict) -> None:
        (root / ".agents").mkdir(parents=True, exist_ok=True)
        (root / ".agents" / "gates.json").write_text(
            json.dumps({"platform": "web", "adapter-hints": hints}), encoding="utf-8")

    def _run(self, root: Path, hint: str, checks: str) -> dict:
        _, payload = instrument_json(
            "scripts/declared-command.py",
            ["--repo", ".", "--owner", "verify", "--hint", hint, "--checks", checks], root)
        return by_check(payload)

    def test_a_declared_command_that_passes_is_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, {"smoke-command": "node -e \"console.log('smoke ok')\""})
            r = self._run(root, "smoke-command", "smoke-test-passes")["smoke-test-passes"]
            self.assertEqual(r["result"], "PASS", r["reason"])

    def test_a_declared_command_that_fails_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, {"smoke-command": "node -e \"console.log('boom'); process.exit(2)\""})
            r = self._run(root, "smoke-command", "smoke-test-passes")["smoke-test-passes"]
            self.assertEqual(r["result"], "FAIL")
            self.assertEqual(r["severity"], "BLOCKER")

    def test_a_missing_row_in_the_map_does_not_inherit_the_others(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, {"billing-harness-commands": {
                "sell-01-activation": "node -e \"console.log('ok')\"",
            }})
            checks = self._run(root, "billing-harness-commands", "sell-01-activation,sell-03-machine-or-account-change")
            self.assertEqual(checks["sell-01-activation"]["result"], "PASS")
            self.assertEqual(checks["sell-03-machine-or-account-change"]["result"], "NOT_VERIFIED")
            self.assertIn("sell-03", checks["sell-03-machine-or-account-change"]["reason"])

    def test_no_hint_at_all_is_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, {"tests-command": "npm test"})
            r = self._run(root, "smoke-command", "smoke-test-passes")["smoke-test-passes"]
            self.assertEqual(r["result"], "NOT_VERIFIED")
            self.assertIn("smoke-command", r["reason"])

    def test_a_silent_command_is_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, {"smoke-command": "node -e \"process.exit(0)\""})
            r = self._run(root, "smoke-command", "smoke-test-passes")["smoke-test-passes"]
            self.assertEqual(r["result"], "NOT_VERIFIED")
            self.assertIn("printed nothing", r["reason"])


class TenantIsolationGoesRed(unittest.TestCase):
    """A declared command that **fails** must give FAIL/BLOCKER, not pass for merely existing."""

    def _repo(self, root: Path, hint: str | None) -> None:
        (root / ".agents").mkdir(parents=True, exist_ok=True)
        hints = {"tenant-isolation-command": hint} if hint else {"tests-command": "npm test"}
        (root / ".agents" / "gates.json").write_text(
            json.dumps({"platform": "web", "adapter-hints": hints}), encoding="utf-8")

    def test_no_declared_command_is_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, None)
            _, payload = instrument_json(
                "skills/security-audit/scripts/tenant_isolation.py", ["--repo", ".", "--platform", "web"], root)
            r = by_check(payload)["sec.tenant-isolation"]
            self.assertEqual(r["result"], "NOT_VERIFIED")
            self.assertIn("tenant-isolation-command", r["reason"])

    def test_a_failing_command_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, "node -e \"console.log('Tenant A -> Tenant B 404'); process.exit(1)\"")
            _, payload = instrument_json(
                "skills/security-audit/scripts/tenant_isolation.py", ["--repo", ".", "--platform", "web"], root)
            r = by_check(payload)["sec.tenant-isolation"]
            self.assertEqual(r["result"], "FAIL")
            self.assertEqual(r["severity"], "BLOCKER")

    def test_a_silent_success_is_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, "node -e \"process.exit(0)\"")
            _, payload = instrument_json(
                "skills/security-audit/scripts/tenant_isolation.py", ["--repo", ".", "--platform", "web"], root)
            self.assertEqual(by_check(payload)["sec.tenant-isolation"]["result"], "NOT_VERIFIED")

    def test_a_proven_command_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, "node -e \"console.log('OK  Tenant A tentar alterar vinho do Tenant B -> 404')\"")
            _, payload = instrument_json(
                "skills/security-audit/scripts/tenant_isolation.py", ["--repo", ".", "--platform", "web"], root)
            r = by_check(payload)["sec.tenant-isolation"]
            self.assertEqual(r["result"], "PASS", r["reason"])
            self.assertTrue(any("cross-tenant assertions" in e for e in r["evidence"]))

    def test_a_desktop_project_is_not_applicable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, "node -e \"process.exit(1)\"")
            _, payload = instrument_json(
                "skills/security-audit/scripts/tenant_isolation.py", ["--repo", ".", "--platform", "desktop"], root)
            self.assertEqual(by_check(payload)["sec.tenant-isolation"]["result"], "NOT_APPLICABLE")


class ThreatModelGoesRed(unittest.TestCase):
    """Cites and proves: `event.id` in backticks is not a citation, and an unprefixed one
    resolves against the project roots (`routes/x.ts` → `src/routes/x.ts`)."""

    def _repo(self, root: Path, doc: str) -> None:
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "threat-model.md").write_text(doc, encoding="utf-8")

    def test_a_dangling_citation_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, "## Controls\n- Session: `src/missing.ts:99`.\n")
            _, payload = instrument_json(
                "skills/security-audit/scripts/threat_model.py", ["--repo", "."], root)
            r = by_check(payload)["sec.threat-model-declared"]
            self.assertEqual(r["result"], "FAIL")
            self.assertTrue(any("missing.ts" in e for e in r["evidence"]))

    def test_a_model_with_no_citation_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, "## Controlos\nEstamos protegidos.\n")
            _, payload = instrument_json(
                "skills/security-audit/scripts/threat_model.py", ["--repo", "."], root)
            self.assertEqual(by_check(payload)["sec.threat-model-declared"]["result"], "FAIL")

    def test_an_identifier_between_backticks_is_not_a_citation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "db.ts").write_text("export const q = 1\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "db.test.mjs").write_text("// teste\n", encoding="utf-8")
            self._repo(root, "## Controlos\n- Unicidade por `event.id` em `src/db.ts:1`, `tests/db.test.mjs`.\n")
            _, payload = instrument_json(
                "skills/security-audit/scripts/threat_model.py", ["--repo", "."], root)
            r = by_check(payload)["sec.threat-model-declared"]
            self.assertEqual(r["result"], "PASS")
            self.assertNotIn("event.id", " ".join(r["evidence"]))

    def test_a_citation_without_a_prefix_resolves_against_the_project_roots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src" / "routes").mkdir(parents=True)
            (root / "src" / "routes" / "auth.ts").write_text("export const a = 1\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "auth.test.mjs").write_text("// teste\n", encoding="utf-8")
            self._repo(root, "## Controlos\n- Sessao em `routes/auth.ts:1`, provado por `tests/auth.test.mjs`.\n")
            _, payload = instrument_json(
                "skills/security-audit/scripts/threat_model.py", ["--repo", "."], root)
            r = by_check(payload)["sec.threat-model-declared"]
            self.assertEqual(r["result"], "PASS", r["reason"])
            self.assertIn("into tests: 1", " ".join(r["evidence"]))


class EvidenceValidatorGoesRed(unittest.TestCase):
    def test_a_pass_without_command_is_downgraded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit = root / ".audit" / "code-review"
            audit.mkdir(parents=True)
            (audit / "code-review--runtime.build-passes.evidence.yaml").write_text(
                "check: runtime.build-passes\nowner: code-review\nproducer: code-review\n"
                "instrument: build-runner\nrule: declared\nmethods:\n  - build-runner\n"
                "evidence: []\nresult: PASS\nconfidence: OBSERVED\n", encoding="utf-8")
            p = run([sys.executable, str(PLUGIN / "skills/audit-app/scripts/validate_evidence.py"),
                     "--repo", str(root)], root)
            self.assertNotEqual(p.returncode, 0, "the validator must demote a PASS without a command")
            self.assertIn("no-log", (p.stdout + p.stderr))


class TrimCheckGoesRed(unittest.TestCase):
    def _repo(self, tmp: str) -> Path:
        root = Path(tmp)
        run(["git", "init", "-q"], root)
        (root / "a.ts").write_text("export const x = 1;\n", encoding="utf-8")
        run(["git", "add", "-A"], root)
        run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "x"], root)
        return root

    def test_a_long_comment_history_and_an_echoed_constant_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            (root / "a.ts").write_text(
                "export const x = 1;\n\nfunction f() {}\n"
                "// one\n// two\n// three\n// four\nfunction g() {}\n"
                "// It previously ran twice.\nfunction h() {}\n"
                "// Wait 250 ms.\nconst WAIT_MS = 250;\n", encoding="utf-8")
            code, payload = instrument_json(
                "skills/close-work/scripts/trim_check.py", ["--repo", "."], root)
            r = by_check(payload)
            self.assertNotEqual(code, 0)
            self.assertEqual(r["trim.comment-budget"]["result"], "FAIL")
            self.assertEqual(r["trim.no-history"]["result"], "FAIL")
            self.assertEqual(r["trim.no-constant-echo"]["result"], "FAIL")

    def test_lines_this_work_did_not_touch_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            code, payload = instrument_json(
                "skills/close-work/scripts/trim_check.py", ["--repo", "."], root)
            self.assertEqual(code, 0)
            self.assertTrue(all(x["result"] == "PASS" for x in payload["results"]))


class EveryInstrumentHasARedCase(unittest.TestCase):
    """The rule, applied to instruments that do not exist yet."""

    def test_every_declared_instrument_is_covered_or_excused(self):
        declared: set[str] = set()
        for manifest in (PLUGIN / "skills").glob("*/instruments.yaml"):
            text = manifest.read_text(encoding="utf-8")
            declared |= set(re.findall(r"^\s*instrument:\s*(\S+)\s*$", text, re.M))

        self.assertTrue(declared, "nenhum instrumento declarado: o teste perdeu o alvo")
        missing = sorted(n for n in declared if n not in RED_CASE and n not in NO_RED_CASE)
        self.assertEqual(
            missing, [],
            "instrument declared without a red case or a reason not to have one: "
            + ", ".join(missing))

    def test_every_red_case_names_a_script_that_exists(self):
        for instrument, (script, _) in RED_CASE.items():
            with self.subTest(instrument=instrument):
                self.assertTrue((PLUGIN / script).is_file(), f"{instrument}: {script} does not exist")

    def test_every_red_case_names_a_test_class_in_this_file(self):
        here = Path(__file__).read_text(encoding="utf-8")
        for instrument, (_, klass) in RED_CASE.items():
            with self.subTest(instrument=instrument):
                self.assertIn(f"class {klass}(", here,
                              f"{instrument}: class {klass} does not exist in this file")

    def test_every_excuse_has_a_reason(self):
        for instrument, reason in NO_RED_CASE.items():
            with self.subTest(instrument=instrument):
                self.assertGreaterEqual(len(reason), 12,
                                        f"{instrument}: reason too short to be a reason")


if __name__ == "__main__":
    unittest.main(verbosity=2)
