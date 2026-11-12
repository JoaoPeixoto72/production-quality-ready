#!/usr/bin/env python3
"""trim_check.py — close-work instrument: what this work wrote that nobody needs.

Comments and documents are read by the next agent, on every visit. A line that
the code already says, that narrates history, or that repeats a constant's value
costs tokens each time and drifts. Scans only the lines this work added (diff
against --since, default HEAD, plus untracked files); --all scans everything.

Config: `owners.close-work.trim` in `<host>/gates.json` (see DEFAULTS): the
project sets its own `comment-lines`, and `header-exempt` names the files whose
opening comment has no budget (default: migrations).
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

HOSTS = (".agents", ".claude")  # the order every owner reads them in
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
    # Files whose opening comment is their only documentation and are never edited
    # again (a forward-only migration): that header has no line budget.
    "header-exempt": ["migrations/*", "*/migrations/*"],
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
TEST_MOD_OPEN = re.compile(r"\bmod\s+\w+\s*\{")
# Lines that carry no text: comment delimiters and rulers (`// -----`, `/* ==== */`).
BARE_DELIMITER = re.compile(r"^\s*(\{?/\*\*?|\*/\}?|\*|//[/!]?|#)?[\s\-=─*#/{}]*$")


def git(repo: Path, *args: str) -> str:
    """`quotepath=off`: an accented name came back quoted and octal-escaped, and was skipped.
    A failing git (a mistyped `--since`) stops here: read as empty, it said "nothing to trim"."""
    p = subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=repo, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        sys.exit(f"git {' '.join(args)}: {p.stderr.strip() or f'exit {p.returncode}'}")
    return p.stdout


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
    # `--relative`: paths from `--repo`, like `ls-files`, and not from the git root.
    for l in git(repo, "diff", "-U0", "--no-color", "--relative", since, "--").splitlines():
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


class Rules:
    """The project's trim config, compiled once."""

    def __init__(self, cfg: dict):
        vis = cfg.get("visible-text") or {}
        self.max_block = int(cfg["comment-lines"])
        self.history = re.compile("|".join(cfg["history"]), re.I)
        self.forbidden = re.compile(vis["forbidden"], re.I) if vis.get("forbidden") else None
        self.ignore = re.compile(vis["ignore"]) if vis.get("ignore") else None
        self.visible_paths = vis.get("paths", [])
        self.skip = cfg["skip"]
        self.header_exempt = cfg.get("header-exempt") or []


class Source:
    """One file this work touched: its lines, which are comment, which are new."""

    def __init__(self, repo: Path, name: str, only: set[int] | None):
        self.name, self.only = name, only
        self.ext = Path(name).suffix.lower()
        self.lines = (repo / name).read_text(encoding="utf-8", errors="replace").splitlines()
        self.is_comment = comment_lines(self.ext, self.lines)
        # An inline `#[cfg(test)] mod x {` starts the tests; `#[cfg(test)] mod x;` lives elsewhere,
        # and `#[cfg(test)]` on a lone fn or struct is not where the tests begin.
        self.tests_from = next((k for k, l in enumerate(self.lines) if TEST_MODULE.search(l)
                                and TEST_MOD_OPEN.search(" ".join(self.lines[k:k + 3]))), len(self.lines))

    def new(self, k: int) -> bool:
        return self.only is None or k + 1 in self.only

    def blocks(self):
        """(start, end) of each run of comment lines."""
        k = 0
        while k < len(self.lines):
            end = k
            while end < len(self.lines) and self.is_comment[end]:
                end += 1
            if end > k:
                yield k, end
            k = max(end, k + 1)


def constant_echo(lines: list[str], k: int, end: int) -> str | None:
    """`NAME = value` when the comment in lines[k:end] repeats the value of the constant below it."""
    m = CONSTANT.match(lines[end]) if end < len(lines) else None
    if not m:
        return None
    values = {v for v in NUMBER.findall(m.group(6)) if len(v) > 1}
    echo = next((v for v in NUMBER.findall(" ".join(lines[k:end])) if v in values), None)
    return f"{m.group(5)} = {echo}" if echo else None


def comment_findings(src: Source, rules: Rules, found: dict[str, list[str]]) -> None:
    header_free = any(fnmatch.fnmatch(src.name, g) for g in rules.header_exempt)
    for k, end in src.blocks():
        if not any(src.new(j) for j in range(k, end)):
            continue
        limit = 2 * rules.max_block if k == 0 else rules.max_block  # a file header may say what the file is
        text_lines = sum(1 for j in range(k, end) if not BARE_DELIMITER.match(src.lines[j]))
        exempt = header_free and not any(not src.is_comment[j] and src.lines[j].strip() for j in range(k))
        if text_lines > limit and k < src.tests_from and not exempt:
            found["trim.comment-budget"].append(f"{src.name}:{k + 1} {text_lines} lines")
        echo = constant_echo(src.lines, k, end)
        if echo:
            found["trim.no-constant-echo"].append(f"{src.name}:{k + 1} repeats {echo}")


def line_findings(src: Source, rules: Rules, found: dict[str, list[str]]) -> None:
    visible = rules.forbidden and any(fnmatch.fnmatch(src.name, g) for g in rules.visible_paths)
    for k, line in enumerate(src.lines):
        if not src.new(k):
            continue
        where = f"{src.name}:{k + 1} {line.strip()[:80]}"
        if (src.is_comment[k] or src.ext in DOCS) and rules.history.search(line):
            found["trim.no-history"].append(where)
        if not visible or src.is_comment[k] or k >= src.tests_from or (rules.ignore and rules.ignore.search(line)):
            continue
        text = " ".join(STRING.findall(line)) if src.ext in {".rs", ".py", ".go"} \
            else re.sub(r"\s//.*$", "", line)
        if rules.forbidden.search(text):
            found["trim.visible-text"].append(where)


def scan(repo: Path, since: str | None) -> dict[str, list[str]]:
    rules = Rules(config(repo))
    found: dict[str, list[str]] = {"trim.comment-budget": [], "trim.no-history": [],
                                   "trim.no-constant-echo": [], "trim.visible-text": []}
    for f, only in sorted(added_lines(repo, since).items()):
        path = repo / f
        if any(fnmatch.fnmatch(f, g) or fnmatch.fnmatch("/" + f, "*/" + g) for g in rules.skip):
            continue
        if not path.is_file() or path.suffix.lower() not in CODE | HASH | SQL | DOCS:
            continue
        src = Source(repo, f, only)
        comment_findings(src, rules, found)
        line_findings(src, rules, found)
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--since", default="HEAD", help="base revision of this work")
    ap.add_argument("--all", action="store_true", help="every tracked line, as if new")
    ap.add_argument("--format", choices=["json", "md"], default="json")
    a = ap.parse_args()
    # A Windows pipe is cp1252: a `→` in a flagged line crashed the report.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
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
