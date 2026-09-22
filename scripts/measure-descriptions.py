#!/usr/bin/env python3
"""
measure-descriptions.py — a única fonte de verdade sobre chars de description.

Uso:
    <interpretador> scripts/measure-descriptions.py <caminho>...

Onde <interpretador> é o comando fixado por --print-interpreter (ver abaixo).
No Windows, `python3` é frequentemente um atalho para a Microsoft Store que
NÃO é interpretador nenhum; este script imprime no cabeçalho da saída o
comando efectivo usado (mesma regra que a Fase 0 do motor de auditoria).

<caminho> é uma pasta com SKILL.md ou uma pasta que contém pastas com
SKILL.md, em qualquer profundidade. Excluídas ao percorrer: `fixtures/`,
`tests/`, `.git/`, `node_modules/`, `.venv/`, `venv/`.

Exit 1 se alguma description ultrapassar o teto (250 por omissão) — o CI
do plugin usa isto como gate.

Regra dura: os números do PLAN.md e das métricas de aceitação vêm daqui.
Nenhum número escrito nos documentos do plugin fica sem o comando que o
produz.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
import platform

EXCLUDED_DIRS = {
    "fixtures",
    "tests",
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
}


def extract_description(text: str) -> str | None:
    """Extract the `description` value from a SKILL.md frontmatter block.

    Handles both folded (`description: >-\\n  ...`) and inline
    (`description: ...`) forms. Returns the value with whitespace collapsed
    to single spaces and trimmed. Returns None if no frontmatter or no
    description field.
    """
    m = re.search(r"^---\n(.*?)\n---", text, re.S | re.M)
    if not m:
        return None
    fm = m.group(1)
    m2 = re.search(
        r"^description:\s*(?P<tag>>-?|\|-?)?\s*(?P<body>.*?)(?=^\S|\Z)",
        fm,
        re.S | re.M,
    )
    if not m2:
        return None
    tag = m2.group("tag")
    body = m2.group("body")
    if tag:
        # Folded block. Strip leading whitespace on each continuation line,
        # then collapse all whitespace to single spaces.
        body = re.sub(r"^\s+", "", body, flags=re.M)
        body = re.sub(r"\s+", " ", body)
    else:
        # Inline. Collapse whitespace too, for consistency with folded.
        body = re.sub(r"\s+", " ", body)
    return body.strip()


def find_skill_files(root: pathlib.Path) -> list[pathlib.Path]:
    """Recursively find SKILL.md files, skipping the excluded directories.

    Uses os.walk-style pruning: when we descend into a directory whose name
    is in EXCLUDED_DIRS, we do not recurse into it.
    """
    if root.is_file() and root.name == "SKILL.md":
        return [root]
    if not root.is_dir():
        return []
    found: list[pathlib.Path] = []
    stack: list[pathlib.Path] = [root]
    while stack:
        d = stack.pop()
        try:
            children = list(d.iterdir())
        except PermissionError:
            continue
        for child in children:
            if child.is_dir():
                if child.name in EXCLUDED_DIRS:
                    continue
                stack.append(child)
            elif child.is_file() and child.name == "SKILL.md":
                found.append(child)
    return sorted(found)


def interpreter_line() -> str:
    """Return a one-line description of the running interpreter for the
    header. Mirrors the auditar-app Fase 0 rule («register the effective
    command and its version»)."""
    vi = sys.version_info
    return (
        f"{sys.executable} — Python "
        f"{vi.major}.{vi.minor}.{vi.micro} on {platform.system()}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", type=pathlib.Path)
    ap.add_argument(
        "--ceiling",
        type=int,
        default=250,
        help="ceiling in chars (default 250 — the host listing truncates "
        "there and skills over budget stop being shown); hard limit 1024",
    )
    ap.add_argument(
        "--print-interpreter",
        action="store_true",
        help="print the effective interpreter and exit "
        "(use to diagnose python3-microsoft-store trap)",
    )
    args = ap.parse_args()

    if args.print_interpreter:
        print(interpreter_line())
        return 0

    if not args.paths:
        ap.error("at least one path required (or --print-interpreter)")

    rows: list[tuple[str, int, str]] = []
    for p in args.paths:
        for skill in find_skill_files(p):
            desc = extract_description(skill.read_text(encoding="utf-8"))
            if desc is None:
                rows.append((str(skill.parent.name), -1, "no-description"))
                continue
            n = len(desc)
            status = (
                "OK"
                if n <= args.ceiling
                else f"OVER-CEILING(+{n - args.ceiling})"
                if n <= 1024
                else f"OVER-HARD(+{n - 1024})"
            )
            rows.append((skill.parent.name, n, status))

    if not rows:
        print("no SKILL.md found under given paths", file=sys.stderr)
        print(f"# interpreter: {interpreter_line()}", file=sys.stderr)
        print(f"# excluded dirs: {sorted(EXCLUDED_DIRS)}", file=sys.stderr)
        return 2

    print(f"# interpreter: {interpreter_line()}")
    print(f"# excluded dirs: {sorted(EXCLUDED_DIRS)}")
    print(f"# ceiling: {args.ceiling} (hard platform limit: 1024)")
    print()

    name_w = max(len(name) for name, _, _ in rows)
    name_w = max(name_w, len("skill"))
    print(f"| {'skill'.ljust(name_w)} | chars | status |")
    print(f"|{'-' * (name_w + 2)}|------:|--------|")
    for name, n, status in rows:
        n_str = "—" if n < 0 else str(n)
        print(f"| {name.ljust(name_w)} | {n_str:>5} | {status} |")

    total = sum(n for _, n, _ in rows if n >= 0)
    print(f"| {'TOTAL'.ljust(name_w)} | {total:>5} |        |")
    print(f"\nFiles measured: {len(rows)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
