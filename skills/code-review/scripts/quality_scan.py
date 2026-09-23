#!/usr/bin/env python3
"""quality_scan.py — code-review maintainability instrument.

Measures what a budget can measure: file length, function length,
control-flow nesting and parameter count, against the budgets the project
declares in `<host>/gates.json` (`owners.code-review.budgets`). What a number
cannot see — names, duplication, indirection, swallowed errors — is the
review-change M axes, not this script.

A committed baseline (`<host>/quality-baseline.json`) turns the budgets into
a ratchet: a debt already recorded passes while it does not grow; a new one
fails. `--write-baseline` records today's debts.

Blind spots, declared: functions are found by pattern in TS/JS/Rust (Python
uses `ast`); a function whose return type is an object literal is measured
as part of its parent; nesting counts control-flow blocks only.

Prints `{results: [...]}` on stdout (the run-all-owners protocol), or a
table with `--format md`. Exit 1 when a budget check fails.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BUDGETS = {"file-lines": 1000, "function-lines": 50, "nesting": 3, "params": 4}
EVIDENCE_CAP = 50
BRACE_LANGS = {".ts": "js", ".tsx": "js", ".js": "js", ".jsx": "js", ".mjs": "js",
               ".cjs": "js", ".rs": "rust"}
PY_EXTS = {".py"}
SKIP_DIRS = {".git", "node_modules", "target", "dist", "build", "coverage", ".venv",
             "venv", "__pycache__", ".audit", ".verify", "vendor", ".next", ".svelte-kit"}
HOSTS = (".agents", ".claude")

CHECKS = {  # check id -> (budget key, what is measured)
    "quality.file-size": ("file-lines", "lines in the file"),
    "quality.function-size": ("function-lines", "lines in the function"),
    "quality.nesting": ("nesting", "control-flow depth inside a function"),
    "quality.params": ("params", "parameters of a function"),
}


@dataclass
class Measure:
    check: str
    path: str
    line: int
    name: str
    value: int

    @property
    def key(self) -> str:
        return self.path if self.check == "quality.file-size" else f"{self.path}::{self.name}"


@dataclass
class Function:
    name: str
    line: int
    end: int = 0
    params: int = 0
    nesting: int = 0


# ------------------------------------------------------------ project config

def find_host(repo: Path) -> Path | None:
    for host in HOSTS:
        if (repo / host / "gates.json").is_file():
            return repo / host
    return None


def load_config(repo: Path) -> tuple[dict, list[str], list[str], bool]:
    """(budgets, ignore-dirs, ignore-globs, budgets-declared)."""
    host = find_host(repo)
    if host is None:
        return dict(DEFAULT_BUDGETS), [], [], False
    gates = json.loads((host / "gates.json").read_text(encoding="utf-8"))
    own = (gates.get("owners") or {}).get("code-review") or {}
    declared = own.get("budgets") or {}
    budgets = {**DEFAULT_BUDGETS, **declared}
    return budgets, own.get("ignore-dirs", []), own.get("ignore-globs", []), bool(declared)


# ------------------------------------------------------------ file selection

def changed_files(repo: Path, since: str) -> set[str]:
    def git(*args: str) -> list[str]:
        out = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
        return [line for line in out.stdout.splitlines() if line]
    return set(git("diff", "--name-only", since)) | set(git("ls-files", "--others", "--exclude-standard"))


def candidate_paths(repo: Path) -> list[str]:
    """What git would commit — so ignored and generated output never counts."""
    try:
        out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                             cwd=repo, capture_output=True, text=True, check=True)
        return sorted(set(out.stdout.splitlines()))
    except (OSError, subprocess.CalledProcessError):
        return sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*") if p.is_file())


def source_files(repo: Path, ignore_dirs: list[str], ignore_globs: list[str],
                 only: set[str] | None):
    skip = SKIP_DIRS | set(ignore_dirs)
    for rel in candidate_paths(repo):
        path = repo / rel
        if path.suffix not in BRACE_LANGS.keys() | PY_EXTS or rel.endswith(".d.ts"):
            continue
        if skip & set(Path(rel).parts[:-1]) or not path.is_file():
            continue
        if any(fnmatch.fnmatch(rel, g) for g in ignore_globs):
            continue
        if only is not None and rel not in only:
            continue
        yield path, rel


# ------------------------------------------------------------ brace languages

STRING_RE = {
    "js": re.compile(r"//[^\n]*|/\*.*?\*/|'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"|`(?:\\.|[^`\\])*`", re.S),
    "rust": re.compile(r"//[^\n]*|/\*.*?\*/|r#*\"(?:.|\n)*?\"#*|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\\n])'", re.S),
}
CONTROL = {
    "js": re.compile(r"^(?:else\s+)?(?:if|else|for|while|do|switch|try|catch|finally)\b"),
    "rust": re.compile(r"^(?:else\s+)?(?:if|else|for|while|loop|match)\b"),
}
JS_KEYWORDS = {"if", "for", "while", "switch", "catch", "return", "new", "function", "typeof"}
JS_METHOD = re.compile(r"^(?:(?:public|private|protected|static|readonly|async|override|abstract|get|set|export|default)\s+)*"
                       r"\*?\s*([A-Za-z_$][\w$]*)\s*(?:<[^()]*>)?\s*\(", re.S)
JS_NAMED = re.compile(r"([A-Za-z_$][\w$]*)\s*[=:]\s*(?:async\s*)?(?:function\b|\(|[A-Za-z_$][\w$]*\s*=>|<)")
RUST_FN = re.compile(r"\bfn\s+([A-Za-z_]\w*)")


def mask(text: str, lang: str) -> str:
    """Blank out comments and string contents, keeping every newline."""
    def blank(m: re.Match) -> str:
        return re.sub(r"[^\n]", " ", m.group(0))
    return STRING_RE[lang].sub(blank, text)


def header_before(code: str, pos: int) -> tuple[str, int]:
    """Text between the previous `;{}` at paren depth 0 and `pos`, and its start."""
    depth = 0
    i = pos - 1
    while i >= 0:
        c = code[i]
        if c == ")":
            depth += 1
        elif c == "(":
            depth -= 1
        elif c in ";{}" and depth <= 0:
            break
        i -= 1
    return code[i + 1:pos], i + 1


def group_after(text: str, start: int) -> str:
    """Content of the balanced `(...)` group opening at or after `start`."""
    open_at = text.find("(", start)
    if open_at < 0:
        return ""
    depth = 0
    for i in range(open_at, len(text)):
        depth += {"(": 1, ")": -1}.get(text[i], 0)
        if depth == 0:
            return text[open_at + 1:i]
    return ""


def count_params(group: str, lang: str) -> int:
    parts, depth, current = [], 0, ""
    for c in group:
        depth += {"(": 1, "[": 1, "{": 1, "<": 1, ")": -1, "]": -1, "}": -1, ">": -1}.get(c, 0)
        if c == "," and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += c
    parts.append(current)
    names = [p.strip() for p in parts if p.strip()]
    if lang == "rust":
        names = [p for p in names if not re.fullmatch(r"&?(?:'\w+\s+)?(?:mut\s+)?self(?:\s*:.*)?", p)]
    return len(names)


def classify(header: str, lang: str) -> tuple[str, str, int]:
    """(kind, name, params) for the block opened after `header`."""
    h = " ".join(header.split())
    h = re.sub(r"^\}?\s*", "", h)
    if CONTROL[lang].match(h):
        return "control", "", 0
    if lang == "rust":
        m = RUST_FN.search(h)
        return ("function", m.group(1), count_params(group_after(h, m.end()), lang)) if m else ("other", "", 0)
    return classify_js(h)


def classify_js(h: str) -> tuple[str, str, int]:
    if h.endswith("=>"):
        named = JS_NAMED.search(h)
        return "function", named.group(1) if named else "<anonymous>", arrow_params(h[:-2].rstrip())
    fn = re.search(r"\bfunction\b\s*\*?\s*([A-Za-z_$][\w$]*)?", h)
    if fn:
        return "function", fn.group(1) or "<anonymous>", count_params(group_after(h, fn.end()), "js")
    m = JS_METHOD.match(h)
    if m and m.group(1) not in JS_KEYWORDS and re.search(r"\)\s*(?::\s*[^=]+)?$", h):
        return "function", m.group(1), count_params(group_after(h, m.end() - 1), "js")
    return "other", "", 0


def arrow_params(before: str) -> int:
    """Parameters of `(a, b): T =>`; a bare `x =>` is one."""
    m = re.search(r"\)\s*(?::[^()]*)?$", before)
    if not m:
        return 1
    close, depth = m.start(), 0
    for i in range(close, -1, -1):
        depth += {")": 1, "(": -1}.get(before[i], 0)
        if depth == 0:
            return count_params(before[i + 1:close], "js")
    return 0


def is_arrow_body(code: str, pos: int) -> bool:
    return code[:pos].rstrip().endswith("=>")


def brace_functions(text: str, lang: str) -> list[Function]:
    code = mask(text, lang)
    done: list[Function] = []
    stack: list[dict] = []
    parens, line = 0, 1
    for pos, c in enumerate(code):
        if c == "\n":
            line += 1
        elif c == "(":
            parens += 1
        elif c == ")":
            parens = max(0, parens - 1)
        elif c == "{":
            parent = stack[-1] if stack else None
            stack.append(open_block(block_kind(code, pos, lang, parens), parens, parent))
            parens = 0
        elif c == "}" and stack:
            block = stack.pop()
            parens = block["parens"]
            if block["fn"] is not None:
                block["fn"].end = line
                done.append(block["fn"])
    return done


def block_kind(code: str, pos: int, lang: str, parens: int) -> tuple[str, Function | None]:
    """What the `{` at `pos` opens: ("function", Function) or ("control"|"other", None)."""
    if parens > 0 and not is_arrow_body(code, pos):
        return "other", None  # an object literal or a type inside a call's arguments
    header, start = header_before(code, pos)
    kind, name, params = classify(header, lang)
    if kind != "function":
        return kind, None
    first = start + len(header) - len(header.lstrip())
    return kind, Function(name, code.count("\n", 0, first) + 1, params=params)


def open_block(opened: tuple[str, Function | None], parens: int, parent: dict | None) -> dict:
    kind, fn = opened
    block = {"parens": parens, "fn": fn, "depth": 0, "owner": fn}
    if fn is not None:
        return block
    block["owner"] = parent["owner"] if parent else None
    block["depth"] = (parent["depth"] if parent else 0) + (1 if kind == "control" else 0)
    if block["owner"] is not None and kind == "control":
        block["owner"].nesting = max(block["owner"].nesting, block["depth"])
    return block


# ------------------------------------------------------------ python

PY_CONTROL = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try, ast.Match)


def python_functions(text: str) -> list[Function]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    found = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = node.args
            names = [p.arg for p in a.posonlyargs + a.args + a.kwonlyargs] + [x.arg for x in (a.vararg, a.kwarg) if x]
            params = len([n for n in names if n not in ("self", "cls")])
            found.append(Function(node.name, node.lineno, node.end_lineno or node.lineno,
                                  params, py_depth(node)))
    return found


def py_depth(node: ast.AST, depth: int = 0) -> int:
    deepest = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        is_elif = isinstance(node, ast.If) and node.orelse == [child] and isinstance(child, ast.If)
        step = 1 if isinstance(child, PY_CONTROL) and not is_elif else 0
        deepest = max(deepest, py_depth(child, depth + step))
    return deepest


# ------------------------------------------------------------ measuring

def measure_file(path: Path, rel: str) -> list[Measure]:
    text = path.read_text(encoding="utf-8", errors="replace")
    found = [Measure("quality.file-size", rel, 1, "", text.count("\n") + 1)]
    lang = BRACE_LANGS.get(path.suffix)
    functions = brace_functions(text, lang) if lang else python_functions(text)
    seen: dict[str, int] = {}
    for fn in functions:
        seen[fn.name] = seen.get(fn.name, 0) + 1
        name = fn.name if seen[fn.name] == 1 else f"{fn.name}#{seen[fn.name]}"
        found += [Measure("quality.function-size", rel, fn.line, name, fn.end - fn.line + 1),
                  Measure("quality.nesting", rel, fn.line, name, fn.nesting),
                  Measure("quality.params", rel, fn.line, name, fn.params)]
    return found


def over_budget(measures: list[Measure], budgets: dict) -> list[Measure]:
    return [m for m in measures if m.value > budgets[CHECKS[m.check][0]]]


def split_by_baseline(debts: list[Measure], baseline: dict) -> tuple[list[Measure], list[Measure]]:
    """(new or grown, tolerated)."""
    new, known = [], []
    for m in debts:
        recorded = baseline.get(m.check, {}).get(m.key)
        (known if recorded is not None and m.value <= recorded else new).append(m)
    return new, known


def baseline_of(debts: list[Measure]) -> dict:
    out: dict[str, dict[str, int]] = {}
    for m in debts:
        out.setdefault(m.check, {})[m.key] = m.value
    return out


# ------------------------------------------------------------ reporting

def results(debts: list[Measure], baseline: dict, budgets: dict, declared: bool) -> list[dict]:
    new, known = split_by_baseline(debts, baseline)
    out = [{"check": "quality.budgets-declared",
            "result": "PASS" if declared else "FAIL",
            "severity": None if declared else "LOW",
            "reason": "budgets in gates.json owners.code-review.budgets" if declared
                      else f"no budgets declared; plugin defaults used: {DEFAULT_BUDGETS}",
            "evidence": []}]
    for check, (key, what) in CHECKS.items():
        mine = [m for m in new if m.check == check]
        tolerated = sum(1 for m in known if m.check == check)
        out.append({"check": check,
                    "result": "FAIL" if mine else "PASS",
                    "severity": "MEDIUM" if mine else None,
                    "reason": f"budget {budgets[key]} {what}; {len(mine)} new or grown, {tolerated} in baseline",
                    "evidence": evidence_lines(mine, budgets[key])})
    failed = any(r["result"] == "FAIL" for r in out[1:])
    out.append({"check": "quality.budgets-met", "result": "FAIL" if failed else "PASS",
                "severity": "MEDIUM" if failed else None,
                "reason": "every size/nesting/params budget met, baseline debts not grown", "evidence": []})
    return [{k: v for k, v in r.items() if v is not None} for r in out]


def evidence_lines(debts: list[Measure], budget: int) -> list[str]:
    worst = sorted(debts, key=lambda m: m.value, reverse=True)
    lines = [f"{m.path}:{m.line} {m.name or '(file)'} {m.value} > {budget}" for m in worst[:EVIDENCE_CAP]]
    if len(worst) > EVIDENCE_CAP:
        lines.append(f"... and {len(worst) - EVIDENCE_CAP} more")
    return lines


def as_markdown(rows: list[dict]) -> str:
    lines = ["| check | result | reason |", "|---|---|---|"]
    for r in rows:
        lines.append(f"| `{r['check']}` | {r['result']} | {r['reason']} |")
        lines += [f"|  |  | {e} |" for e in r.get("evidence", [])]
    return "\n".join(lines)


# ------------------------------------------------------------ entry point

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--since", help="only files changed since this git ref (plus untracked)")
    ap.add_argument("--baseline", help="default: <host>/quality-baseline.json")
    ap.add_argument("--write-baseline", action="store_true", help="record today's debts and exit")
    ap.add_argument("--format", choices=("json", "md"), default="json")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")

    repo = Path(a.repo).resolve()
    budgets, ignore_dirs, ignore_globs, declared = load_config(repo)
    host = find_host(repo) or repo / HOSTS[0]
    baseline_path = Path(a.baseline) if a.baseline else host / "quality-baseline.json"
    only = changed_files(repo, a.since) if a.since else None

    measures = [m for path, rel in source_files(repo, ignore_dirs, ignore_globs, only)
                for m in measure_file(path, rel)]
    debts = over_budget(measures, budgets)
    if a.write_baseline:
        baseline_path.write_text(json.dumps(baseline_of(debts), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"{len(debts)} debts recorded in {baseline_path}")
        return 0

    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.is_file() else {}
    rows = results(debts, baseline, budgets, declared)
    print(as_markdown(rows) if a.format == "md" else json.dumps({"results": rows}, indent=2))
    return 1 if any(r["result"] == "FAIL" and r["check"] != "quality.budgets-declared" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
