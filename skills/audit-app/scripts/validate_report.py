#!/usr/bin/env python3
"""Structural validation of an audit report.

Checks only what the document itself decides: vocabulary tokens, IDs that
exist in the registry, one state per row, counts that match the table, and
the verdict truth table. It does **not** check whether evidence is true, a
justification enough, or a `NOT_APPLICABLE` well founded — parsing cannot
decide that, and claiming it would be the error this validator exists to catch.

Exit codes:
  0  structurally valid
  1  problems found
  2  cannot analyse (not a report, or it does not name its contract)
 64  usage error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_PROBLEMS = 1
EXIT_CANNOT_ANALYSE = 2
EXIT_USAGE = 64

STATES = {"PENDING", "PROVEN", "CLEARED", "UNPROVEN", "NOT_APPLICABLE"}
METHOD_COVERAGE = {"COMPLETE", "PARTIAL", "SAMPLE"}
EVIDENCE_TYPES = {"EXECUTION", "TEST", "MEASUREMENT", "STATIC_ANALYSIS",
                  "READING", "DOCUMENT", "EXTERNAL_SOURCE"}
NO_EVIDENCE = {"-", "—", "NO_PROOF"}
PRODUCT_VERDICTS = {"PASS", "CONCERNS", "FAIL"}
COVERAGE_VERDICTS = {"COMPLETE", "PARTIAL", "BLOCKED"}
PRIORITIES = {"P0", "P1", "P2", "P3"}
GLOBALS = {"global"}

DESTINATION = "docs/audits"

# Columns the checks read; `Artifact` and `Note` are in the format but nothing reads them.
USED_COLUMNS = ("id", "state", "gate", "evidence", "coverage")

# A finding baseline: what IDs are taken. `evals-run.md` cites IDs without owning them.
BASELINES_WITH_FINDINGS = ("resolved-findings.md", "accepted-risks.md", "last-audit.md")


def current_contract() -> str | None:
    """SHA-256 of the plugin's `CONTRACTS.md`, LF-normalised (CONTRACTS §6)."""
    p = Path(__file__).resolve()
    for candidate in [p.parents[3], p.parents[2], p.parents[1]]:
        contract = candidate / "CONTRACTS.md"
        if contract.is_file():
            raw = contract.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            return hashlib.sha256(raw).hexdigest()
    return None


# An obligation ID: `SEC-01` (registry v1) or `owner::check` (contract v2).
RE_OBLIGATION_ID = re.compile(r"[A-Z0-9]+-\d+|[a-z][a-z0-9-]*::[A-Za-z0-9._-]+")
RE_CANONICAL_V2 = re.compile(r"^\|\s*`([a-z][a-z0-9-]*)`\s*\|\s*`([^`]+)`(?:\s*…\s*`([^`]+)`)?\s*\|", re.M)
RE_FOR_CHECKS = re.compile(r"^\s+-\s+([A-Za-z0-9._-]+)\s*$", re.M)
RE_HASH = re.compile(r"SHA-256[\s:`*]*([0-9a-f]{64})", re.I)
RE_COUNTS = re.compile(
    r"`?PROVEN`?:\s*~?(\d+).*?`?CLEARED`?:\s*~?(\d+).*?"
    r"`?UNPROVEN`?:\s*~?(\d+).*?`?NOT_APPLICABLE`?:\s*~?(\d+)", re.S)
# Any separator between the two axes (`·`, `|`, `-`, `–`): typography is not validated.
RE_VERDICT = re.compile(
    r"^\|?\s*`?([A-Za-z][A-Za-z0-9\-]*)`?\s*[|:]\s*(?:Product:\s*)?\*{0,2}(PASS|CONCERNS|FAIL)\*{0,2}"
    r"\s*[|·\-–]\s*(?:Coverage:\s*)?\*{0,2}(COMPLETE|PARTIAL|BLOCKED)\*{0,2}"
    r"\s*(?:\((\d+)\s*/\s*(\d+)\))?", re.M)
RE_FINDING = re.compile(r"^###\s+\*{0,2}([A-Z0-9]+-F\d+)\*{0,2}\s*[—-]", re.M)
RE_FINDING_ID = re.compile(r"\b([A-Z0-9]+-F\d+)\b")
# A baseline block's date: in the heading (`## 2026-09-09 — full`) or a field.
RE_DATE = re.compile(r"^#{2,3} (\d{4}-\d{2}-\d{2})|\*\*(?:Date|Resolved on)\*\*:\s*(\d{4}-\d{2}-\d{2})", re.M)
RE_PRIORITY = re.compile(r"\*\*Priority\*\*:\s*\*{0,2}(P[0-3])\*{0,2}")
RE_AREA = re.compile(r"\*\*Area\*\*:\s*\*{0,2}`?([A-Za-z][A-Za-z0-9\-]*)`?")
RE_MODIFIER = re.compile(r"\b(PROVEN|CLEARED|UNPROVEN|NOT_APPLICABLE)\s*\(([^)]+)\)")
RE_FENCE = re.compile(r"^```.*?^```", re.M | re.S)


def registry_v2(plugin_root: Path) -> dict:
    """Contract v2 obligations, read from the plugin itself.

    Critical: the `owner::check` rows of CONTRACTS §7.4 (a range expands over the
    owner's checks with the same prefix). Non-critical: every `for-checks` entry,
    plus the `<owner>.instrument-available` the runner writes.
    """
    registry: dict[str, dict] = {}
    declared: dict[str, list[str]] = {}
    for manifest in sorted((plugin_root / "skills").glob("*/instruments.yaml")):
        owner = manifest.parent.name
        declared[owner] = RE_FOR_CHECKS.findall(manifest.read_text(encoding="utf-8"))
        for check in declared[owner] + [f"{owner}.instrument-available"]:
            registry[f"{owner}::{check}"] = {"module": owner, "critical": False}

    contract = (plugin_root / "CONTRACTS.md").read_text(encoding="utf-8")
    start = contract.find("### 7.4")
    end = contract.find("\n### ", start + 1)
    for owner, first, last in RE_CANONICAL_V2.findall(contract[start:end]):
        checks = [first]
        if last:
            prefix = re.match(r"[a-z]+-", first)
            checks = [c for c in declared.get(owner, [])
                      if prefix and c.startswith(prefix.group(0))] or [first, last]
        for check in checks:
            registry[f"{owner}::{check}"] = {"module": owner, "critical": True}
    return registry


class _Parser(argparse.ArgumentParser):
    def error(self, message: str):
        self.print_usage(sys.stderr)
        print(f"error: {message}", file=sys.stderr)
        raise SystemExit(EXIT_USAGE)


def cells(rest: str) -> list[str]:
    return [c.strip() for c in rest.rstrip("|").split("|")]


def clean(token: str) -> str:
    return token.replace("*", "").replace("`", "").strip()


def earlier_findings(root: Path, before: str | None = None) -> set[str]:
    """Finding IDs the baselines knew **before** `before` (the report's date).

    A report's own findings reach the baselines after it is written, so they must
    not count against it. An undated block cannot be placed in time and does not
    count: erring towards not accusing keeps the validator worth reading.
    """
    seen: set[str] = set()
    for name in BASELINES_WITH_FINDINGS:
        try:
            text = (root / "baselines" / name).read_text(encoding="utf-8")
        except OSError:
            continue
        for block in re.split(r"(?=^#{2,3} )", text, flags=re.M):
            if before is not None:
                m = RE_DATE.search(block)
                date = (m.group(1) or m.group(2)) if m else None
                if date is None or date >= before:
                    continue
            seen |= set(RE_FINDING_ID.findall(block))
    return seen


def without_code_fences(text: str) -> str:
    """Fenced blocks blanked, line count kept: the proposed baseline blocks are not the report's findings."""
    return RE_FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def finding_blocks(text: str):
    """`(id, block)` for each `### XXX-Fnn — ...` up to the next heading."""
    headings = [m.start() for m in re.finditer(r"^#{2,4}\s", text, re.M)]
    for m in RE_FINDING.finditer(text):
        after = [h for h in headings if h > m.start()]
        yield m.group(1), text[m.start():after[0] if after else len(text)]


def priorities_by_module(text: str) -> tuple[dict[str, set[str]], dict[str, str]]:
    """Each finding's priority, under the module its `**Area**` names.

    Returns `(by_module, without_area)`; a finding without an area belongs to no
    module and counts for the global verdict.
    """
    by_module: dict[str, set[str]] = {}
    without_area: dict[str, str] = {}
    for fid, block in finding_blocks(text):
        mp = RE_PRIORITY.search(block)
        if not mp:
            continue
        ma = RE_AREA.search(block)
        if ma:
            by_module.setdefault(clean(ma.group(1)).lower(), set()).add(mp.group(1))
        else:
            without_area[fid] = mp.group(1)
    return by_module, without_area


def validate(text: str, registry: dict, path: Path,
             current_hash: str | None = None,
             earlier: set[str] | None = None,
             known: set[str] | None = None) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    warnings: list[str] = []
    error = problems.append
    earlier = earlier or set()
    # "Does this ID exist?" (known, same day included) is not "was it taken before me?" (earlier).
    known = known if known is not None else earlier

    if DESTINATION.split("/")[-1] not in path.as_posix().split("/"):
        warnings.append(f"outside `{DESTINATION}/` — the index cannot find it by address")

    mh = RE_HASH.search(text)
    if not mh:
        error("no contract `SHA-256` — a version alone does not identify the rules")
    elif current_hash and mh.group(1).lower() != current_hash:
        warnings.append(f"contract hash `{mh.group(1)[:12]}…` is not the current "
                        f"`{current_hash[:12]}…` — the rules have changed since")

    for m in RE_MODIFIER.finditer(text):
        if clean(m.group(2)).upper() not in METHOD_COVERAGE:
            error(f"state with modifier `{m.group(0)}` — one state per row, the rest in Note")

    # The obligations table is the report's source of truth; columns are found by header name.
    seen: dict[str, int] = {}
    counts: dict[str, int] = {s: 0 for s in STATES}
    modules_in_table: set[str] = set()
    columns: dict[str, int] | None = None

    for line in text.splitlines():
        raw = line.strip()
        if not raw.startswith("|"):
            columns = None
            continue
        row = cells(raw.lstrip("|"))
        keys = [clean(c).lower() for c in row]
        if "id" in keys and "state" in keys:
            columns = {name: i for i, name in enumerate(keys)}
            for name in USED_COLUMNS:
                if name not in columns:
                    error(f"obligations table without the `{name}` column — what depends on it would go unchecked")
            continue
        if set("".join(keys)) <= {"-", ":", " "} or columns is None:
            continue

        def cell(name: str) -> str:
            i = columns.get(name)
            return clean(row[i]) if i is not None and i < len(row) else ""

        oid = cell("id")
        if not RE_OBLIGATION_ID.fullmatch(oid):
            continue
        if len(row) < len(columns):
            error(f"`{oid}`: row with {len(row)} cells for {len(columns)} columns — the missing ones go unchecked")
        state = cell("state")
        if not state:
            continue
        if state not in STATES:
            error(f"`{oid}`: state `{state}` outside the vocabulary")
            continue
        if state == "PENDING":
            error(f"`{oid}`: `PENDING` — no obligation is left unanalysed at the end")
        seen[oid] = seen.get(oid, 0) + 1
        counts[state] += 1

        if oid not in registry:
            error(f"`{oid}`: ID not in the gate registry")
            continue
        meta = registry[oid]
        if meta["module"]:
            modules_in_table.add(meta["module"])

        declared = cell("gate").lower()
        if declared in {"yes", "critical", "no"}:
            is_critical = declared in {"yes", "critical"}
            if is_critical != meta["critical"]:
                error(f"`{oid}`: row says critical={is_critical}, registry says {meta['critical']}")

        evidence = cell("evidence")
        if evidence and evidence not in NO_EVIDENCE:
            for part in re.split(r"[+/]", evidence):
                part = part.strip().split("(")[0].strip()
                if part and part not in EVIDENCE_TYPES:
                    error(f"`{oid}`: evidence type `{part}` outside the vocabulary")

        coverage = cell("coverage")
        if coverage and coverage not in {"-", "—"}:
            if coverage not in METHOD_COVERAGE:
                error(f"`{oid}`: method coverage `{coverage}` outside the vocabulary")
            elif coverage == "SAMPLE" and state == "CLEARED":
                error(f"`{oid}`: CLEARED with SAMPLE coverage — a sample does not close a universal obligation")

    if not seen:
        error("no obligations table — there is no report to validate")
        return problems, warnings

    # Missing critical gates: decidable, the registry knows each one's module.
    for oid, meta in sorted(registry.items()):
        if meta["critical"] and meta["module"] in modules_in_table and oid not in seen:
            error(f"`{oid}`: critical gate of `{meta['module']}` missing from the table")

    for oid, n in sorted(seen.items()):
        if n > 1:
            error(f"`{oid}`: appears {n} times in the table")

    mc = RE_COUNTS.search(text)
    if not mc:
        warnings.append("no counts line (`PROVEN: n · CLEARED: n · ...`)")
    else:
        if "~" in mc.group(0):
            error("counts with `~`: they are counted in the table, not estimated")
        stated = {"PROVEN": int(mc.group(1)), "CLEARED": int(mc.group(2)),
                  "UNPROVEN": int(mc.group(3)), "NOT_APPLICABLE": int(mc.group(4))}
        for state, n in stated.items():
            if n != counts[state]:
                error(f"`{state}` count: the summary says {n}, the table has {counts[state]}")

    # A priority belongs to its finding's module, not to the whole document.
    outside_fences = without_code_fences(text)
    by_module, without_area = priorities_by_module(outside_fences)
    every_priority = {p for ps in by_module.values() for p in ps} | set(without_area.values())

    verdict_lines = []
    for mv in RE_VERDICT.finditer(text):
        module, product, coverage, num, den = mv.groups()
        if product in PRODUCT_VERDICTS and coverage in COVERAGE_VERDICTS:
            verdict_lines.append((module, clean(module).lower(), product, coverage, num, den))

    modules = {n for _, n, *_ in verdict_lines if n not in GLOBALS}
    failed_modules = sorted(n for _, n, p, *_ in verdict_lines if p == "FAIL" and n not in GLOBALS)
    # In a single-module report a finding without `**Area**` has an obvious owner.
    only = next(iter(modules)) if len(modules) == 1 else None
    for fid in sorted(without_area):
        warnings.append(
            f"`{fid}`: has `**Priority**` but no `**Area**` — "
            + (f"assigned to `{only}`, this report's only module" if only
               else "counts for the global verdict and no module"))

    for module, name, product, coverage, num, den in verdict_lines:
        is_global = name in GLOBALS
        priorities = every_priority if is_global else by_module.get(name, set())
        if name == only:
            priorities = priorities | set(without_area.values())
        if (priorities & {"P0", "P1"}) and product != "FAIL":
            error(f"`{module}`: {product} with an open P0/P1 — the truth table requires FAIL")
        if num is None:
            error(f"`{module}`: coverage `{coverage}` without the fraction (X/Y)")
        elif coverage == "COMPLETE" and num != den:
            error(f"`{module}`: COMPLETE with {num}/{den} — COMPLETE requires all")
        if is_global and failed_modules and product != "FAIL":
            error(f"global `{product}` with `{failed_modules[0]}` in FAIL — "
                  "the SKILL.md aggregation requires FAIL")

    # A cited finding exists in this report or in the baselines' memory.
    declared_findings = set(RE_FINDING.findall(outside_fences))
    for fid in sorted(set(RE_FINDING_ID.findall(outside_fences)) - declared_findings - known):
        error(f"`{fid}`: cited without a `### {fid} — ...` section and unknown to the "
              "baselines — neither this report's nor an earlier audit's")

    # A taken ID is either the same defect again (say recurrence) or another one (a free number).
    for fid, block in finding_blocks(outside_fences):
        if fid in earlier and "recurr" not in block.lower():
            error(f"`{fid}`: number already used by an earlier audit and this report does "
                  "not mark it as a recurrence — if it is another defect, give it a free number")

    return problems, warnings


def main(argv: list[str] | None = None) -> int:
    ap = _Parser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report", nargs="?", help="the report's .md file")
    ap.add_argument("--contract", action="store_true",
                    help="print the installed CONTRACTS.md SHA-256 and exit — the report header copies it")
    ap.add_argument("--gates", default=None,
                    help="v1 registry as JSON; by default, the plugin's own v2 registry")
    args = ap.parse_args(argv)

    current_hash = current_contract()
    if current_hash is None:
        print("error: the plugin's CONTRACTS.md was not found — no rules to judge by", file=sys.stderr)
        return EXIT_CANNOT_ANALYSE
    if args.contract:
        print(current_hash)
        return EXIT_OK
    if not args.report:
        ap.error("the report is missing")

    path = Path(args.report)
    if not path.is_file():
        print(f"error: {path} is not a file", file=sys.stderr)
        return EXIT_CANNOT_ANALYSE
    plugin_root = Path(__file__).resolve().parents[3]
    if args.gates:
        gates = Path(args.gates)
        if not gates.is_file():
            print(f"error: gate registry not found at {gates}", file=sys.stderr)
            return EXIT_CANNOT_ANALYSE
        registry = json.loads(gates.read_text(encoding="utf-8"))
    elif (plugin_root / "CONTRACTS.md").is_file():
        registry = registry_v2(plugin_root)
    else:
        print(f"error: no --gates and no CONTRACTS.md in {plugin_root}", file=sys.stderr)
        return EXIT_CANNOT_ANALYSE

    text = path.read_text(encoding="utf-8", errors="replace")
    # Without the contract hash nothing is validated: dozens of "errors" would hide the real ones.
    if not RE_HASH.search(text):
        print(f"# Validation of {path.name}\n")
        print("No `Contract: SHA-256 <digest>` — no way to know which rules to judge by.")
        print("The current digest comes from `validate_report.py --contract`.")
        print("\nCANNOT ANALYSE")
        return EXIT_CANNOT_ANALYSE

    skill_root = Path(__file__).resolve().parent.parent
    m_date = re.match(r"(\d{4}-\d{2}-\d{2})", path.name)
    problems, warnings = validate(
        text, registry, path, current_hash,
        earlier_findings(skill_root, m_date.group(1) if m_date else None),
        earlier_findings(skill_root))
    print(f"# Validation of {path.name}\n")
    print(f"## Problems: {len(problems)}")
    for p in problems:
        print(f"  ERROR    {p}")
    print(f"\n## Warnings: {len(warnings)}")
    for w in warnings:
        print(f"  warning  {w}")
    print()
    if problems:
        print("REPORT STRUCTURALLY INVALID")
    else:
        print("REPORT STRUCTURALLY VALID — CONTENT AND SUFFICIENCY OF EVIDENCE NOT VALIDATED")
    return EXIT_OK if not problems else EXIT_PROBLEMS


def _run(fn) -> int:
    try:
        code = fn()
        sys.stdout.flush()
        return code
    except BrokenPipeError:
        import os
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0


if __name__ == "__main__":
    sys.exit(_run(main))
