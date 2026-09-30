#!/usr/bin/env python3
"""tenant-isolation — o isolamento entre tenants provado pelo comando do projeto.

`sec.tenant-isolation` é um gate crítico: "recursos privados isolados pelo
principal; entre tenants é 404, provado por teste". Um instrumento do plugin
não sabe que teste do projeto é esse — sabe que *tem* de ser um comando que
corre e falha quando o isolamento parte.

Portanto o projeto declara-o em `<host>/gates.json`:

    "adapter-hints": {
      "tenant-isolation-command": "node tests/security_and_invitations.test.mjs"
    }

O instrumento corre esse comando e lê o resultado:
  - sem comando declarado      → NOT_VERIFIED/missing-instrument (a lacuna é dita)
  - comando sai != 0           → FAIL/BLOCKER (o isolamento partiu)
  - comando sai 0 sem output   → NOT_VERIFIED/no-output (nada prova que correu)
  - comando sai 0 com output   → PASS (o log é a evidência)
  - plataforma != web          → NOT_APPLICABLE/platform

    python tenant_isolation.py --repo . --platform web

Saída: JSON no stdout, resumo no stderr, exit 0 (o veredicto vai no JSON).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HINT = "tenant-isolation-command"
PLATFORMS = ("web",)


def host_dir(repo: Path) -> Path | None:
    for rel in (".agents", ".claude"):
        if (repo / rel / "gates.json").is_file():
            return repo / rel
    return None


def declared_command(repo: Path) -> str | None:
    host = host_dir(repo)
    if host is None:
        return None
    try:
        gates = json.loads((host / "gates.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    hints = gates.get("adapter-hints") or {}
    value = hints.get(HINT)
    return value if isinstance(value, str) and value.strip() else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--platform", default="web")
    ap.add_argument("--command", help="sobrepõe o comando declarado em gates.json")
    a = ap.parse_args(argv)

    repo = Path(a.repo).resolve()
    evidence: list[str] = []

    if a.platform not in PLATFORMS:
        result, severity = "NOT_APPLICABLE", ""
        reason = (f"no private multi-tenant surface declared for `{a.platform}`; the check is "
                  f"{'/'.join(PLATFORMS)}-only")
    else:
        command = (a.command or "").strip() or declared_command(repo)
        if not command:
            result, severity = "NOT_VERIFIED", ""
            reason = (f"missing-instrument: no `{HINT}` declared in `adapter-hints` of the project's "
                      "gates.json — the command that exercises cross-tenant access and asserts 404")
        else:
            try:
                p = subprocess.run(command, cwd=repo, shell=True, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=1800)
                output = (p.stdout or "") + (p.stderr or "")
                code = p.returncode
            except subprocess.TimeoutExpired:
                output, code = "timeout after 1800s", 124
            log = repo / ".audit" / "security-audit" / "sec.tenant-isolation.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(f"$ {command}\n\n{output}", encoding="utf-8")

            crossed = [l.strip() for l in output.splitlines() if "Tenant" in l and "404" in l]
            if code != 0:
                result, severity = "FAIL", "BLOCKER"
                reason = (f"`{command}` exited {code}: the command that proves cross-tenant isolation "
                          "fails, so the isolation it exercises is broken or the test no longer covers it")
                evidence += [f"output tail: {l}" for l in output.strip().splitlines()[-6:]]
            elif not output.strip():
                result, severity = "NOT_VERIFIED", ""
                reason = (f"`{command}` exited 0 but printed nothing: an empty run does not show what was "
                          "exercised")
            else:
                result, severity = "PASS", ""
                reason = (f"`{command}` exited 0; the command is the project's declared proof that a "
                          "cross-tenant access answers 404")
                evidence += [f"cross-tenant assertions seen: {len(crossed)}"]
                evidence += [f"  {l}" for l in crossed[:4]]
            evidence.append(f"log: .audit/security-audit/sec.tenant-isolation.log")

    out = {
        "repo": str(repo),
        "results": [{
            "check": "sec.tenant-isolation",
            "result": result,
            "severity": severity,
            "reason": reason,
            "evidence": evidence,
        }],
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"  {result:15} sec.tenant-isolation               {reason[:86]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
