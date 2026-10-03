#!/usr/bin/env python3
"""trim_check.py — close-work instrument: what this work wrote that nobody needs.

Comments and documents are read by the next agent, on every visit. A line that
the code already says, that narrates history, or that repeats a constant's value
costs tokens each time and drifts. Scans only the lines this work added (diff
against --since, default HEAD, plus untracked files); --all scans everything.

Config: `owners.close-work.trim` in `<host>/gates.json` (see DEFAULTS).
Prints `{results: [...]}`, or lines with `--format md`. Exit 1 on a finding.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

HOSTS = (".claude", ".agents")
DEFAULTS = {
    "comment-lines": 3,
    "history": [
        r"\b(we|it|this|they) used to\b", r"\bpreviously\b", r"\bwas (changed|replaced|renamed|moved)\b",
        r"\bno longer\b(?! (exists|matches|fits))", r"\bnow (we|it) \w+s?\b instead\b",
        r"\bin (v|version )\d+\.\d+",
        r"\bpassou a\b", r"\bpassaram a\b", r"\bdeixou de (ser|ter)\b", r"\bdeixaram de (ser|ter)\b",
        r"\bj[aá] foi um\b", r"\bchegou a ser\b", r"\bantigamente\b", r"\bdantes\b",
        r"\bat[eé] hoje\b", r"\bfoi (trocad|substitu[ií]d)[oa]\b", r"\bmudou para\b",
    ],
    "skip": ["node_modules/*", "target/*", "dist/*", "build/*", "vendor/*", "*.lock",
             "package-lock.json", ".claude/*", ".agents/*", "*/tests/*", "*/testes/*", "*.min.*"],
    "visible-text": None,  # {"paths": [globs], "forbidden": regex, "ignore": regex}
}
CODE = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".rs", ".css", ".scss", ".go",
        ".java", ".kt", ".swift", ".c", ".cc", ".cpp", ".h", ".cs"}
HASH = {".py", ".sh", ".toml", ".yaml", ".yml", ".ps1", ".rb"}
SQL = {".sql"}
DOCS = {".md"}
CONSTANT = re.compile(r"^\s*(pub(\([^)]*\))?\s+)?(export\s+)?(const|static|final)\s+([A-Z][A-Z0-9_]+)\b[^=]*=\s*([^;]*)")
NUMBER = re.compile(r"\b\d+(?:[.,]\d+)?\b")
STRING = re.compile(r'"(?:[^"\\]|\\.)*"')
TEST_MODULE = re.compile(r"#\[cfg\(test\)\]")
# Lines that carry no text: comment delimiters and rulers (`// -----`, `/* ==== */`).
BARE_DELIMITER = re.compile(r"^\s*(\{?/\*\*?|\*/\}?|\*|//[/!]?|#)?[\s\-=─*#/{}]*$")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def config(repo: Path) -> dict:
    cfg = dict(DEFAULTS)
    for host in HOSTS:
        p = repo / host / "gates.json"
        if p.exists():
            own = json.loads(p.read_text(encoding="utf-8")).get("owners", {}).get("close-work", {})
            cfg.update(own.get("trim", {}))
            break
    return cfg


def comment_lines(ext: str, lines: list[str]) -> list[bool]:
    """Which lines are comment, following /* */ across lines."""
    out, block = [], False
    for line in lines:
        t = line.strip()
        if block:
            block = "*/" not in t
            out.append(True)
        elif ext in HASH:
            out.append(t.startswith("#") and not t.startswith("#!") and not t.startswith("#["))
        elif ext in SQL:
            out.append(t.startswith("--"))
        elif ext in CODE and re.match(r"\{?/\*", t):
            block = "*/" not in t
            out.append(True)
        else:
            out.append(ext in CODE and t.startswith("//"))
    return out


def added_lines(repo: Path, since: str | None) -> dict[str, set[int] | None]:
    """file -> added line numbers; None means every line (new file, or --all)."""
    if since is None:
        return {f: None for f in git(repo, "ls-files").splitlines() if f}
    out: dict[str, set[int] | None] = {}
    current, n = None, 0
    for l in git(repo, "diff", "-U0", "--no-color", since, "--").splitlines():
        if l.startswith("+++ "):
            current = l[6:] if l.startswith("+++ b/") else None
        elif l.startswith("@@"):
            n = int(re.search(r"\+(\d+)", l).group(1))
        elif l.startswith("+") and current:
            out.setdefault(current, set()).add(n)
            n += 1
    for f in git(repo, "ls-files", "--others", "--exclude-standard").splitlines():
        if f:
            out[f] = None
    return out


def scan(repo: Path, since: str | None) -> dict[str, list[str]]:
    cfg = config(repo)
    history = re.compile("|".join(cfg["history"]), re.I)
    vis = cfg.get("visible-text") or {}
    forbidden = re.compile(vis["forbidden"], re.I) if vis.get("forbidden") else None
    ignore = re.compile(vis["ignore"]) if vis.get("ignore") else None
    max_block = int(cfg["comment-lines"])
    found: dict[str, list[str]] = {"trim.comment-budget": [], "trim.no-history": [],
                                   "trim.no-constant-echo": [], "trim.visible-text": []}

    for f, only in sorted(added_lines(repo, since).items()):
        path = repo / f
        ext = path.suffix.lower()
        if any(fnmatch.fnmatch(f, g) or fnmatch.fnmatch("/" + f, "*/" + g) for g in cfg["skip"]):
            continue
        if not path.is_file() or ext not in CODE | HASH | SQL | DOCS:
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        is_comment = comment_lines(ext, lines)
        new = (lambda k: True) if only is None else (lambda k: k + 1 in only)
        tests_from = next((k for k, l in enumerate(lines) if TEST_MODULE.search(l)), len(lines))

        k = 0
        while k < len(lines):
            if not is_comment[k]:
                k += 1
                continue
            end = k
            while end < len(lines) and is_comment[end]:
                end += 1
            touched = any(new(j) for j in range(k, end))
            limit = 2 * max_block if k == 0 else max_block  # a file header may say what the file is
            text_lines = sum(1 for j in range(k, end) if not BARE_DELIMITER.match(lines[j]))
            if touched and text_lines > limit and k < tests_from:
                found["trim.comment-budget"].append(f"{f}:{k + 1} {text_lines} lines")
            m = CONSTANT.match(lines[end]) if end < len(lines) else None
            if m and touched:
                values = {v for v in NUMBER.findall(m.group(6)) if len(v) > 1}
                said = NUMBER.findall(" ".join(lines[k:end]))
                echo = next((v for v in said if v in values), None)
                if echo:
                    found["trim.no-constant-echo"].append(f"{f}:{k + 1} repeats {m.group(5)} = {echo}")
            k = end

        for k, line in enumerate(lines):
            if not new(k):
                continue
            if (is_comment[k] or ext in DOCS) and history.search(line):
                found["trim.no-history"].append(f"{f}:{k + 1} {line.strip()[:80]}")
            if forbidden and not is_comment[k] and k < tests_from and \
                    any(fnmatch.fnmatch(f, g) for g in vis.get("paths", [])) and \
                    not (ignore and ignore.search(line)):
                text = " ".join(STRING.findall(line)) if ext in {".rs", ".py", ".go"} \
                    else re.sub(r"\s//.*$", "", line)
                if forbidden.search(text):
                    found["trim.visible-text"].append(f"{f}:{k + 1} {line.strip()[:80]}")
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--since", default="HEAD", help="base revision of this work")
    ap.add_argument("--all", action="store_true", help="every tracked line, as if new")
    ap.add_argument("--format", choices=["json", "md"], default="json")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    found = scan(repo, None if a.all else a.since)
    failed = any(found.values())
    if a.format == "md":
        for check, items in found.items():
            for item in items:
                print(f"{check}  {item}")
        print("nothing to trim" if not failed else
              f"\n{sum(map(len, found.values()))} places: trim them, or say why each stays.")
    else:
        print(json.dumps({"results": [
            {"check": c, "result": "FAIL" if items else "PASS", "evidence": items[:200],
             "command": f"trim_check.py --since {a.since}" if not a.all else "trim_check.py --all"}
            for c, items in found.items()]}, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
