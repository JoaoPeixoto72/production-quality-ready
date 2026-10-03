#!/usr/bin/env python3
"""threat-model-check — the threat model cites its proofs, and the proofs exist.

A file merely existing is not evidence: the document must **cite** each
control's proof (`path:line` into the code, and the test exercising it), and
every citation must resolve. A threat model with no citation fails.

    python threat_model.py --repo .

JSON on stdout, summary on stderr, exit 0 (the verdict is in the JSON).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DOC_CANDIDATES = ("docs/threat-model.md", "THREAT_MODEL.md", "docs/seguranca/threat-model.md")

# `src/x.ts:123`, `routes/y.ts` (relative to `src/`), `migrations/0033_x.sql:7` — a
# path, optionally with a line. Extensions are a list, not `\w{1,6}`, so `event.id` is not a citation.
CITATION = re.compile(r"`([A-Za-z0-9_][\w./-]*\.([A-Za-z0-9]{1,8}))(?::(\d+))?`")
TEST_PATH = re.compile(r"(?:^|/)(?:tests?|__tests__)/|\.(?:test|spec)\.", re.IGNORECASE)

# Extensions that count as files (`.id` and `.all` do not).
CODE_EXT = {
    'ts', 'tsx', 'js', 'jsx', 'mjs', 'cjs', 'sql', 'json', 'md', 'py', 'css', 'html',
    'toml', 'yaml', 'yml', 'rs', 'go', 'rb', 'php', 'java', 'kt', 'swift', 'sh', 'ps1',
    'txt', 'env', 'example', 'sample', 'xml', 'vue', 'svelte',
}

# A citation like `routes/x.ts` implies a code root; these are tried before calling it dangling.
ROOTS = ('', 'src/', 'src/routes/', 'src/lib/', 'tests/', 'scripts/', 'migrations/', 'public/')


def find_doc(repo: Path, explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        p = p if p.is_absolute() else repo / p
        return p if p.is_file() else None
    for rel in DOC_CANDIDATES:
        if (repo / rel).is_file():
            return repo / rel
    return None


def citations_of(text: str) -> list[tuple[str, int | None]]:
    out: list[tuple[str, int | None]] = []
    for m in CITATION.finditer(text):
        path, ext, line = m.group(1), m.group(2).lower(), m.group(3)
        if ext not in CODE_EXT:
            continue
        pair = (path, int(line) if line else None)
        if pair not in out:
            out.append(pair)
    return out


def resolve(repo: Path, path: str) -> Path | None:
    """The file a citation points at, trying the project's roots."""
    for root in ROOTS:
        candidate = repo / (root + path)
        if candidate.is_file():
            return candidate
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--doc", help="threat model path (otherwise the usual candidates)")
    a = ap.parse_args(argv)

    repo = Path(a.repo).resolve()
    evidence: list[str] = []

    doc = find_doc(repo, a.doc)
    if doc is None:
        result, severity = "FAIL", "HIGH"
        reason = (f"no threat model found at any of {', '.join(DOC_CANDIDATES)}: "
                  "there is no declared boundary, no adversary list and nothing to hold the controls to")
        evidence.append("a threat model is a versioned file; the check is not about its length")
    else:
        rel_doc = doc.relative_to(repo).as_posix()
        text = doc.read_text(encoding="utf-8", errors="replace")
        cites = citations_of(text)
        dangling: list[str] = []
        tests = 0
        for path, line in cites:
            target = resolve(repo, path)
            if target is None:
                dangling.append(f"{path} (file missing)")
                continue
            if TEST_PATH.search(path):
                tests += 1
            if line is not None:
                total = len(target.read_text(encoding="utf-8", errors="replace").splitlines())
                if line > total:
                    dangling.append(f"{path}:{line} (file has {total} lines)")
        evidence.append(f"doc: {rel_doc}; citations: {len(cites)}; into tests: {tests}")

        if not cites:
            result, severity = "FAIL", "HIGH"
            reason = (f"{rel_doc} cites no proof: a threat model whose controls point at nothing "
                      "cannot be held to anything")
        elif dangling:
            result, severity = "FAIL", "HIGH"
            reason = (f"{len(dangling)} citation(s) in {rel_doc} do not resolve; a control that cites "
                      "code that moved is a control nobody re-checked")
            evidence += [f"dangling: {d}" for d in dangling[:8]]
        elif tests == 0:
            result, severity = "FAIL", "MEDIUM"
            reason = (f"{rel_doc} cites code but no test: a control with no test is a claim that has "
                      "never been exercised")
        else:
            result, severity = "PASS", ""
            reason = (f"{rel_doc} cites {len(cites)} proof(s), {tests} of them into tests, and every "
                      "citation resolves")

    out = {
        "repo": str(repo),
        "results": [{
            "check": "sec.threat-model-declared",
            "result": result,
            "severity": severity,
            "reason": reason,
            "evidence": evidence,
        }],
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"  {result:15} sec.threat-model-declared         {reason[:86]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
