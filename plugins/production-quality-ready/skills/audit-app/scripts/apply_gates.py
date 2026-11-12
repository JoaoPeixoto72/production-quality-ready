#!/usr/bin/env python3
"""Apply the gates of CONTRACTS §7 to the evidence in `.audit/`, in code.

Reads `.audit/**/*.evidence.yaml` through `validate_evidence.py` (so a file the
contract does not admit never counts), then decides, with no judgement left to
the model:

  §4.3  coverage per owner, always as a fraction: BLOCKED (n/m), PARTIAL (n/m),
        COMPLETE (m/m); an owner without canonical checks is BLOCKED (—/?)
  §4.4  dedup by `root-cause:` only — the highest severity of the merged counts once
  §5.4  `platform:` must be declared in gates.json, and every owner that has
        canonical checks must be declared there (applicable or `not-applicable`
        with a reason); otherwise the run aborts
  §7.1  the predicates no-open, all-pass-in-owner, coverage-complete,
        conditional and gate
  §7.3  the standard gates (`references/gates.spec.json`) plus any gate the
        project adds in gates.json

Read-only: writes nothing to `.audit/`, runs nothing against the repo, and two
runs over the same files give the same verdict (§4.2).

Usage:
  python apply_gates.py --repo . [--plugin <root>] [--gate production-ready] [--json]

Exit: 0 every evaluated gate is open, 1 at least one is closed, 2 the run
cannot be judged (no gates.json, no platform, an owner undeclared).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_evidence as ve  # noqa: E402

HERE = Path(__file__).resolve().parent
REFS = HERE.parent / "references"
SEVERITIES = ["BLOCKER", "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
RESOLVED = {"PASS", "FAIL", "WAIVED", "NOT_APPLICABLE"}
ALL_APPLICABLE = "<all-applicable-owners>"


@dataclass
class Finding:
    owner: str
    check: str
    result: str
    severity: str
    root_cause: str
    paths: list = field(default_factory=list)


@dataclass
class Coverage:
    owner: str
    state: str          # COMPLETE | PARTIAL | BLOCKED | NOT_APPLICABLE
    n: int | None
    m: int | None
    missing: list = field(default_factory=list)
    reason: str = ""

    def label(self) -> str:
        if self.state == "NOT_APPLICABLE":
            return f"NOT_APPLICABLE ({self.reason})"
        if self.m is None:
            return f"BLOCKED (—/?) {self.reason}"
        return f"{self.state} ({self.n}/{self.m})"


class Abort(Exception):
    """The run cannot be judged; exit 2 with the reason."""


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def applies(tag: str, platform: str) -> bool:
    return platform == "both" or tag == "both" or tag == platform


class Judge:
    def __init__(self, repo: Path, plugin: Path, today=None):
        self.repo = repo
        self.gates, gates_path = ve.load_gates(repo)
        if self.gates is None:
            raise Abort("gates.json missing or unreadable (.agents/ or .claude/) — run bootstrap-project")
        self.platform = str(self.gates.get("platform", "")).strip()
        if self.platform not in ("web", "desktop", "both"):
            raise Abort("platform-undeclared: gates.json needs platform: web | desktop | both (CONTRACTS §5.4)")
        reg = load_json(REFS / "registry.json")
        self.canonical: dict[str, dict[str, str]] = reg["canonical"]
        self.declared: dict = {ve.canonical_owner(k): (v or {}) for k, v in (self.gates.get("owners") or {}).items()}
        missing = sorted(o for o in self.canonical if o not in self.declared)
        if missing:
            raise Abort("owner-undeclared-in-gates: declare each as applicable or with "
                        f"`not-applicable: <reason>` — {', '.join(missing)}")
        self.verdicts = [ve.validate_file(p, repo, plugin, self.platform, ve.load_waivers(self.gates), today)
                         for p in ve.iter_evidence(repo / ".audit")]
        self.raw = {v.path: ve.parse_yaml_min((repo / v.path).read_text(encoding="utf-8", errors="replace"))
                    for v in self.verdicts}
        spec = load_json(REFS / "gates.spec.json")["gates"]
        self.gate_defs = {g["name"]: g for g in spec}
        for g in self.gates.get("gates") or []:
            if isinstance(g, dict) and g.get("name") not in self.gate_defs:
                self.gate_defs[g["name"]] = g  # a project adds gates; it cannot redefine the standard ones
        self._memo: dict[str, tuple[bool, list]] = {}

    # ------------------------------------------------------------ owners

    def not_applicable(self, owner: str) -> str:
        cfg = self.declared.get(owner)
        if isinstance(cfg, dict) and str(cfg.get("not-applicable", "")).strip():
            return "declared: " + str(cfg["not-applicable"]).strip()
        checks = self.canonical.get(owner, {})
        if checks and not any(applies(t, self.platform) for t in checks.values()):
            return f"platform {self.platform}"
        return ""

    def applicable_owners(self) -> list[str]:
        return [o for o in self.canonical if not self.not_applicable(o)]

    def by_owner(self, owner: str) -> list:
        return [v for v in self.verdicts if v.owner == owner]

    def coverage(self, owner: str) -> Coverage:
        why = self.not_applicable(owner)
        if why:
            return Coverage(owner, "NOT_APPLICABLE", None, None, reason=why)
        checks = self.canonical.get(owner)
        if not checks:
            return Coverage(owner, "BLOCKED", None, None, reason="no-canonical-registry")
        wanted = [c for c, t in checks.items() if applies(t, self.platform)]
        resolved = {v.check for v in self.by_owner(owner) if v.result_effective in RESOLVED}
        missing = [c for c in wanted if c not in resolved]
        n, m = len(wanted) - len(missing), len(wanted)
        state = "COMPLETE" if n == m else ("BLOCKED" if n == 0 else "PARTIAL")
        return Coverage(owner, state, n, m, missing)

    # ---------------------------------------------------------- findings

    def findings(self) -> list[Finding]:
        """Open FAILs after §4.4: only an explicit `root-cause:` merges two files."""
        merged: dict[str, Finding] = {}
        out: list[Finding] = []
        for v in self.verdicts:
            if v.result_effective != "FAIL":
                continue
            d = self.raw[v.path]
            sev = str(d.get("severity", "")).strip().upper() or "UNKNOWN"
            rc = str(d.get("root-cause", "")).strip()
            if rc and rc in merged:
                f = merged[rc]
                f.paths.append(v.path)
                if sev in SEVERITIES and (f.severity not in SEVERITIES or
                                          SEVERITIES.index(sev) < SEVERITIES.index(f.severity)):
                    f.severity = sev
                continue
            f = Finding(v.owner, v.check, v.result_effective, sev, rc, [v.path])
            out.append(f)
            if rc:
                merged[rc] = f
        return out

    # -------------------------------------------------------- predicates

    def _owners_arg(self, arg) -> list[str]:
        if arg == ALL_APPLICABLE:
            return self.applicable_owners()
        return [ve.canonical_owner(o) for o in (arg if isinstance(arg, list) else [arg])]

    def no_open(self, sevs) -> tuple[bool, list]:
        sevs = {s.upper() for s in sevs}
        # A FAIL without a severity cannot prove it is minor: it counts as open.
        hits = [f for f in self.findings() if f.severity in sevs or f.severity == "UNKNOWN"]
        return not hits, [f"open {f.severity}: {f.owner}::{f.check} ({', '.join(f.paths)})" for f in hits]

    def coverage_complete(self, arg) -> tuple[bool, list]:
        why = []
        for o in self._owners_arg(arg):
            c = self.coverage(o)
            if c.state not in ("COMPLETE", "NOT_APPLICABLE"):
                tail = f" — missing {', '.join(c.missing)}" if c.missing else ""
                why.append(f"{o}: {c.label()}{tail}")
        return not why, why

    def all_pass_in_owner(self, arg) -> tuple[bool, list]:
        why = []
        for o in self._owners_arg(arg):
            if self.not_applicable(o):
                continue
            vs = [v for v in self.by_owner(o) if v.result_effective != "NOT_APPLICABLE"]
            if not vs:
                why.append(f"{o}: no evidence (absence is never approval)")
                continue
            bad = [v for v in vs if v.result_effective not in ("PASS", "WAIVED")]
            why += [f"{o}::{v.check} is {v.result_effective}" for v in bad]
        return not why, why

    def condition(self, expr: str) -> bool:
        m = re.fullmatch(r"\s*project\.([A-Za-z0-9_-]+)\s*==\s*(.+?)\s*", str(expr))
        if not m:
            raise Abort(f"conditional: cannot read `{expr}` (expected project.<key> == <value>)")
        want = m.group(2).strip().strip("'\"")
        have = self.gates.get(m.group(1))
        if isinstance(have, bool):
            return str(have).lower() == want.lower()
        return str(have) == want

    def requirement(self, req: dict) -> tuple[bool, list]:
        (name, arg), = req.items()
        if name == "no-open":
            return self.no_open(arg)
        if name == "coverage-complete":
            return self.coverage_complete(arg)
        if name == "all-pass-in-owner":
            return self.all_pass_in_owner(arg)
        if name == "gate":
            ok, _ = self.gate(arg)
            return ok, [] if ok else [f"gate {arg} is closed"]
        if name == "conditional":
            if not self.condition(arg.get("when", "")):
                return True, []
            return self.requires(arg.get("require", []))
        raise Abort(f"unknown predicate `{name}` (CONTRACTS §7.1 has five)")

    def requires(self, reqs: list) -> tuple[bool, list]:
        ok, why = True, []
        for r in reqs:
            r_ok, r_why = self.requirement(r)
            ok, why = ok and r_ok, why + r_why
        return ok, why

    def gate(self, name: str) -> tuple[bool, list]:
        if name not in self._memo:
            if name not in self.gate_defs:
                raise Abort(f"gate `{name}` is not defined (standard: {', '.join(self.gate_defs)})")
            self._memo[name] = (False, ["cycle"])  # a gate requiring itself never opens
            self._memo[name] = self.requires(self.gate_defs[name].get("requires", []))
        return self._memo[name]

    def requested(self) -> list[str]:
        names = [g if isinstance(g, str) else g.get("name") for g in self.gates.get("gates") or []]
        return [n for n in names if n] or list(self.gate_defs)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--plugin", default=None, help="plugin root (default: autodetect)")
    ap.add_argument("--gate", action="append", help="evaluate only this gate (repeatable)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # an old interpreter keeps its encoding; output is still ASCII-safe enough
        pass
    repo = Path(a.repo).resolve()
    plugin = ve.find_plugin(repo, a.plugin)
    if plugin is None:
        print("plugin root not found (pass --plugin)", file=sys.stderr)
        return 2
    try:
        j = Judge(repo, plugin)
        names = a.gate or j.requested()
        results = {n: j.gate(n) for n in names}
    except Abort as e:
        print(f"cannot judge: {e}", file=sys.stderr)
        return 2

    owners = sorted(set(j.canonical) | {v.owner for v in j.verdicts if v.owner})
    cov = {o: j.coverage(o) for o in owners}
    if a.json:
        print(json.dumps({
            "platform": j.platform,
            "gates": {n: {"open": ok, "why": why} for n, (ok, why) in results.items()},
            "coverage": {o: c.label() for o, c in cov.items()},
            "open-findings": [f.__dict__ for f in j.findings()],
            "files": len(j.verdicts),
            "downgraded": sum(1 for v in j.verdicts if v.downgraded),
        }, indent=2, ensure_ascii=False))
    else:
        print(f"platform={j.platform} files={len(j.verdicts)} "
              f"downgraded={sum(1 for v in j.verdicts if v.downgraded)}\n\nCoverage:")
        for o, c in cov.items():
            print(f"  {o:22} {c.label()}")
        print("\nGates:")
        for n, (ok, why) in results.items():
            print(f"  {'OPEN  ' if ok else 'CLOSED'} {n}")
            for w in why:
                print(f"         - {w}")
    return 0 if all(ok for ok, _ in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
