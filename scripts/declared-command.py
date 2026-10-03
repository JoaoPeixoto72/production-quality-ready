#!/usr/bin/env python3
"""declared-command — run the command the project declares as proof.

Some obligations need an instrument only the project can write (the app's
smoke test, the sales paths, tenant isolation). The plugin knows what to do
with the result: run it, keep the log, turn the exit code into a verdict.

The project declares the command in `<host>/gates.json`, under `adapter-hints`:

    "adapter-hints": {
      "smoke-command": "pwsh -NoProfile -File scripts/smoke.ps1",
      "billing-harness-commands": {
        "sell-01-activation": "node tests/billing.test.mjs",
        "sell-05-refund-cancel": "node tests/billing.test.mjs"
      }
    }

The value is either:
  - **a string** — one command for every obligation asked;
  - **an object** — one command per obligation; one without a command is
    `NOT_VERIFIED` with the reason, never a PASS inherited from the others.

Verdict per obligation:
  - no command declared        → NOT_VERIFIED (the gap is said, not filled)
  - command exits != 0         → FAIL/BLOCKER
  - command exits 0, no output → NOT_VERIFIED (nothing proves it ran)
  - command exits 0 with output → PASS (the log is the evidence)

    python declared-command.py --repo . --owner verify --hint smoke-command \\
        --checks smoke-test-passes

JSON on stdout, summary on stderr, exit 0 (the verdict is in the JSON).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

TIMEOUT = 1800


def host_dir(repo: Path) -> Path | None:
    for rel in (".agents", ".claude"):
        if (repo / rel / "gates.json").is_file():
            return repo / rel
    return None


def hints(repo: Path) -> dict:
    host = host_dir(repo)
    if host is None:
        return {}
    try:
        gates = json.loads((host / "gates.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    value = gates.get("adapter-hints") or {}
    return value if isinstance(value, dict) else {}


def command_for(hint: object, check: str) -> str | None:
    if isinstance(hint, str):
        return hint.strip() or None
    if isinstance(hint, dict):
        value = hint.get(check)
        return value.strip() if isinstance(value, str) and value.strip() else None
    return None


def run_command(repo: Path, command: str) -> tuple[int, str]:
    try:
        p = subprocess.run(command, cwd=repo, shell=True, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=TIMEOUT)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {TIMEOUT}s"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--owner", required=True)
    ap.add_argument("--hint", required=True)
    ap.add_argument("--checks", required=True, help="comma-separated obligations")
    ap.add_argument("--command", help="overrides the declared value (tests and manual use)")
    a = ap.parse_args(argv)

    repo = Path(a.repo).resolve()
    checks = [c.strip() for c in a.checks.split(",") if c.strip()]
    declared = a.command if a.command else hints(repo).get(a.hint)

    results = []
    for check in checks:
        command = (a.command or "").strip() or command_for(declared, check)
        if not command:
            results.append({
                "check": check, "result": "NOT_VERIFIED", "severity": "",
                "reason": (f"missing-instrument: no command declared for `{check}` under "
                           f"`adapter-hints.{a.hint}` in the project's gates.json"),
                "evidence": [],
            })
            continue

        code, output = run_command(repo, command)
        log = repo / ".audit" / a.owner / f"{a.hint}-{check}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(f"$ {command}\n\n{output}", encoding="utf-8")
        log_rel = f".audit/{a.owner}/{a.hint}-{check}.log"
        evidence = [f"log: {log_rel}", f"exit: {code}"]

        if code != 0:
            results.append({
                "check": check, "result": "FAIL", "severity": "BLOCKER",
                "reason": (f"`{command}` exited {code}: the command the project declares as proof of "
                           f"`{check}` fails"),
                "evidence": evidence + [f"output tail: {l}" for l in output.strip().splitlines()[-5:]],
            })
        elif not output.strip():
            results.append({
                "check": check, "result": "NOT_VERIFIED", "severity": "",
                "reason": f"`{command}` exited 0 but printed nothing: an empty run proves nothing",
                "evidence": evidence,
            })
        else:
            results.append({
                "check": check, "result": "PASS", "severity": "",
                "reason": (f"`{command}` exited 0; the project declares this command as its proof of "
                           f"`{check}`"),
                "evidence": evidence,
            })

    out = {"repo": str(repo), "results": results}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    for r in results:
        print(f"  {r['result']:15} {r['check']:34} {r['reason'][:80]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
