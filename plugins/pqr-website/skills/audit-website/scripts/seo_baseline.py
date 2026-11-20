#!/usr/bin/env python3
"""seo_baseline.py — audit-website, the SEO regression ratchet.

A site's SEO does not only break in one shot; it drifts. A `noindex` that a
deploy added, a canonical a CMS rewrote, a schema block that stopped parsing —
each is a `PASS` that silently became a `FAIL`. This instrument compares the
current `seo-audit-report.json` (from `seo/run_seo_audit.mjs`) against a
committed baseline and reports the drift.

Like the maintainability ratchet: **existing debt may not grow**. A finding that
was `PASS` (or was absent, i.e. new) and is now `FAIL` is a regression. A
finding already `FAIL` in the baseline is known debt, not a new one — it stops
failing only when it is fixed or the baseline is rewritten.

It is a **comparison** instrument: it does not crawl and does not judge the
checks themselves; it reads two reports and decides what changed.

Checks decided here:

  web.seo-no-regression   no finding went from PASS/WARN (or new) to FAIL

Output: JSON on stdout, human summary on stderr, exit 0.

Usage:
  python seo_baseline.py --repo . [--report PATH] [--baseline PATH]
  python seo_baseline.py --repo . --write-baseline
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPORT_DEFAULTS = (".audit/audit-website/seo-audit-report.json", "seo-audit-report.json")
# The baseline is committed with the project, next to its gates.json (as quality_scan's is):
# .audit/<owner>/seo-baseline.json is where the runner files this instrument's own output.
HOSTS = (".agents", ".claude")
BASELINE_NAME = "seo-baseline.json"


def finding(result, reason, evidence=None, severity=""):
    return {"check": "web.seo-no-regression", "result": result, "severity": severity,
            "reason": reason, "evidence": evidence or []}


def host_dir(root: Path) -> Path:
    for host in HOSTS:
        if (root / host / "gates.json").is_file():
            return root / host
    return root / HOSTS[0]


def first_existing(root: Path, rels) -> Path | None:
    for rel in rels:
        p = root / rel
        if p.is_file():
            return p
    return None


def statuses(path: Path) -> dict[str, str] | None:
    """id -> status. Reads a `seo-audit-report.json` (`findings` is a list) or a
    baseline written by `--write-baseline` (`findings` is already the id -> status
    map). None when it does not parse."""
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None
    findings = data.get("findings")
    if isinstance(findings, dict):
        return {str(k): str(v).upper() for k, v in findings.items()}
    if isinstance(findings, list):
        out: dict[str, str] = {}
        for f in findings:
            if isinstance(f, dict) and f.get("id"):
                out[str(f["id"])] = str(f.get("status", "")).upper()
        return out
    return None


def compare(current: dict[str, str], base: dict[str, str], baseline_path: Path) -> dict:
    """A FAIL the baseline did not already record as FAIL is a regression."""
    regressions = sorted(fid for fid, st in current.items() if st == "FAIL" and base.get(fid) != "FAIL")
    known = sorted(fid for fid, st in current.items() if st == "FAIL" and base.get(fid) == "FAIL")
    if regressions:
        return finding("FAIL",
                       f"{len(regressions)} SEO regression(s): a finding that was PASS/WARN "
                       f"(or is new) is now FAIL",
                       [f"regression: {r} ({base.get(r, 'new')} -> FAIL)" for r in regressions],
                       severity="HIGH")
    ev = [f"compared {len(current)} finding(s) against {baseline_path}"]
    ev += [f"known debt (unchanged FAIL): {k}" for k in known]
    return finding("PASS", f"no regression: {len(current)} finding(s) compared; "
                           f"{len(known)} known FAIL unchanged", ev)


def decide(report_path: Path | None, baseline_path: Path, write_baseline: bool) -> dict:
    if report_path is None or not report_path.is_file():
        return finding("NOT_VERIFIED", "missing-instrument: no seo-audit-report.json found; run "
                                       "`seo/run_seo_audit.mjs` first")
    current = statuses(report_path)
    if current is None:
        return finding("NOT_VERIFIED", f"the report at {report_path} has no readable `findings` array")
    if write_baseline:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(json.dumps({"findings": current}, indent=2, ensure_ascii=False) + "\n",
                                 encoding="utf-8")
        return finding("NOT_APPLICABLE",
                       f"baseline written: {len(current)} finding(s) recorded at {baseline_path}")
    base = statuses(baseline_path) if baseline_path.is_file() else None
    if base is None:
        return finding("NOT_VERIFIED", f"no baseline at {baseline_path}; record one with --write-baseline")
    return compare(current, base, baseline_path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--report", default=None, help="seo-audit-report.json (default: autodetect)")
    ap.add_argument("--baseline", default=None, help=f"baseline file (default: <host>/{BASELINE_NAME})")
    ap.add_argument("--write-baseline", action="store_true",
                    help="record the current report as the baseline, then stop")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001 — a stream that cannot be reconfigured keeps its encoding
        pass

    repo = Path(a.repo).resolve()
    report_path = Path(a.report) if a.report else first_existing(repo, REPORT_DEFAULTS)
    baseline_path = Path(a.baseline) if a.baseline else host_dir(repo) / BASELINE_NAME
    results = [decide(report_path, baseline_path, a.write_baseline)]

    print(json.dumps({"repo": str(repo), "results": results}, indent=2, ensure_ascii=False))
    for r in results:
        print(f"  {r['result']:15} {r['check']:28} {r['reason'][:80]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
