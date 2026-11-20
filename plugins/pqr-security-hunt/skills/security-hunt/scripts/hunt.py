#!/usr/bin/env python3
"""hunt.py — the instrument of `security-hunt`: ledger, proof and evidence.

A hunt is judgement; this script is what keeps the judgement honest. It holds
the run to the repository (every cited line must still say what the claim says),
to its budget (agents launched never exceed the approved number), to
independence (the agent that found a candidate never confirms it), and to proof
(a confirmed finding is a test of the project's own that fails on the current
commit for the reason the claim gives).

    python hunt.py check      [--repo .]
    python hunt.py record     <agent-id> <answer.json> [--plan] [--repo .]
    python hunt.py stale      [--repo .]
    python hunt.py prove      <fingerprint> [--repo .]
    python hunt.py reprove    [--repo .]
    python hunt.py adopt      <fingerprint> <test_path> --command "<cmd>" [--found-at <sha>]
                              [--baseline-setup "<cmd>"] [--expect "<msg>"] [--no-baseline] [--repo .]
    python hunt.py rebaseline [<fingerprint>] [--baseline-setup "<cmd>"] [--expect "<msg>"] [--repo .]
    python hunt.py emit       [--repo .]

Files, all under `<repo>/.audit/security-hunt/` (gitignored with `.audit/`):
  plan.json      scope, budget, agents launched, external sources, coverage units
  findings.json  one record per fingerprint
  proofs/        the red tests and their logs

`check`      validates both files against the repo and the class catalogue; its
             `warnings` name open findings one verifier can settle together.
`record`     writes a hunter's or the critic's JSON answer into the ledger, after
             re-reading every cited line; a wrong answer is refused whole.
`stale`      lists covered units whose code or card changed since they were read.
`prove`      copies one proof test into place, runs its command, removes it, and
             records the outcome: red (fails for the stated reason), held (passes:
             the control held), broken (fails for another reason).
`reprove`    runs every recorded proof again: re-verification costs no agent.
`adopt`      after a fix: runs a committed regression test of the project and, if it
             passes on HEAD and does not pass on `found_at` (the baseline, in a
             temporary worktree), marks the finding fixed with that test as its proof.
`rebaseline` runs that baseline for findings already fixed; their state stays.
`emit`       writes one FAIL evidence file per `security-audit` check from the
             confirmed findings; it refuses while `check` reports an error.

JSON on stdout, summary on stderr. Exit 0 when the ledger is valid or the action
ran; 1 when it is invalid or the action was refused.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from hunt_baseline import BASELINES, Baseline, Rebaseline, baseline_record, held_refusal, rebaseline
from hunt_core import CATALOGUE, CLAIM_FIELDS, EXTERNAL, FINDERS, HUNT, ROLES, catalogue, commit_of, \
    dirty_cited, fingerprint, head_of, inside, load, log_error, norm, now, outcome_of, \
    regression_refusal, resolve_step, run_command, save, slug, write_log
from hunt_record import Answer, record, stale

OWNER, PRODUCER, INSTRUMENT = "security-audit", "security-hunt", "hunt-proof"
RULE_VERSION = "owasp-asvs-5.0"

# The `security-audit` checks a hunt may fail, with their ASVS 5.0 chapter. A card
# naming a check outside this map is a catalogue defect (`check` reports it).
CHECK_RULE = {
    "sec.tenant-isolation": "V8.2",
    "sec.access-control-default-deny": "V8",
    "sec.session-integrity": "V7",
    "sec.auth-strength": "V6",
    "sec.input-validated": "V2.2",
    "sec.business-logic-abuse": "V2.3",
    "sec.anti-automation": "V2.4",
    "sec.file-uploads-safe": "V5",
    "sec.data-at-rest": "V14",
    "sec.csp-strict": "V3",
    "sec.errors-no-leak": "V16.5",
    "sec.crypto-primitives-justified": "V11",
    "sec.api-surface-declared": "V4",
}
SEVERITIES = ["BLOCKER", "CRITICAL", "HIGH", "MEDIUM", "LOW"]
NEEDS_IMPACT = {"BLOCKER", "CRITICAL", "HIGH"}
UNIT_STATES = {"planned", "in_progress", "covered", "candidate", "blocked", "deferred", "out_of_scope"}
FINDING_STATES = {"candidate", "confirmed", "needs_validation", "rejected", "fixed"}
OPEN_STATES = ("candidate", "confirmed", "needs_validation")
AGENT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
CITED = re.compile(r"([\w@.-]+(?:/[\w@.-]+)*\.[A-Za-z0-9]+):(\d+)")


# ------------------------------------------------------------------ check

@dataclass
class Ctx:
    """What every rule of `check` reads, and the list it writes to."""
    repo: Path
    cards: dict
    head: str
    agents: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)

    def err(self, msg: str) -> None:
        self.errors.append(msg)


def check(repo: Path) -> dict:
    plan = load(repo / HUNT / "plan.json", None)
    if plan is None:
        return {"ok": False, "errors": [f"{HUNT.as_posix()}/plan.json missing: plan before hunting"],
                "summary": {}}
    findings = load(repo / HUNT / "findings.json", [])
    ctx = Ctx(repo, catalogue(), head_of(repo))
    catalogue_errors(ctx)
    budget = plan_errors(ctx, plan)
    by_fp = fingerprint_index(ctx, findings)
    units = plan.get("units", []) or []
    ids = [str(u.get("id", "")) for u in units]
    for uid in sorted({i for i in ids if not i or ids.count(i) > 1}):
        ctx.err(f"plan.units: id `{uid}` missing or repeated")
    linked: set[str] = set()
    for i, u in enumerate(units):
        linked |= unit_errors(ctx, u, f"plan.units[{i}]", by_fp)
    for i, f in enumerate(findings):
        finding_errors(ctx, f, f"findings[{i}]")
        if f.get("fingerprint") not in linked:
            ctx.err(f"findings[{i}]: `{f.get('fingerprint')}` is linked to no unit")
    return {"ok": not ctx.errors, "errors": ctx.errors, "warnings": duplicate_warnings(findings),
            "summary": summarise(ctx, units, findings, budget)}


def duplicate_warnings(findings: list) -> list[str]:
    """Open findings that one verifier can settle together: the same class at the same
    sink file, or claims that name the same control file. Advice, never an error."""
    groups: dict[tuple, list[str]] = {}
    for f in (f for f in findings if f.get("state") in OPEN_STATES):
        fp, sink = str(f.get("fingerprint")), ((f.get("trace") or [{}])[-1]).get("path", "")
        groups.setdefault(("sink", str(f.get("class")), str(sink)), []).append(fp)
        cited = CITED.search(str((f.get("claim") or {}).get("control", "")))
        if cited:
            groups.setdefault(("control", "", cited.group(1)), []).append(fp)
    out = []
    for (kind, cls, path), fps in sorted(groups.items()):
        if len(fps) < 2:
            continue
        shared = f"class {cls} and sink {path}" if kind == "sink" else f"the control in {path}"
        out.append(f"{', '.join(fps)} share {shared} — one verifier can settle both")
    return out


def catalogue_errors(ctx: Ctx) -> None:
    if not ctx.cards:
        ctx.err(f"catalogue: no class card found under {CATALOGUE}")
    for cls, chk in ctx.cards.items():
        if chk not in CHECK_RULE:
            ctx.err(f"catalogue: class {cls} names {chk}, which no security-audit check maps")


def plan_errors(ctx: Ctx, plan: dict) -> int:
    """Checks the plan's head and records the agents; returns the approved budget."""
    tm = inside(ctx.repo, str(plan.get("threat_model", "")))
    if tm is None or not tm.is_file():
        ctx.err(f"plan.threat_model: `{plan.get('threat_model')}` is not a file in the repo — the hunt starts from it")
    if not norm(plan.get("scope", "")):
        ctx.err("plan.scope: empty — the person approves a scope before any agent runs")
    budget = (plan.get("budget") or {}).get("agents")
    if not isinstance(budget, int) or budget < 1:
        ctx.err("plan.budget.agents: a positive integer the person approved")
        budget = 0
    for i, a in enumerate(plan.get("agents", []) or []):
        aid, role = str(a.get("id", "")), str(a.get("role", ""))
        if not AGENT_ID.match(aid):
            ctx.err(f"plan.agents[{i}].id: `{aid}` is not a lowercase agent id")
        if aid in ctx.agents:
            ctx.err(f"plan.agents[{i}].id: `{aid}` launched twice — each agent is recorded once")
        if role not in ROLES:
            ctx.err(f"plan.agents[{i}].role: `{role}` is not hunter, verifier or critic")
        ctx.agents[aid] = role
    launched = sum(1 for r in ctx.agents.values() if r in ROLES)
    for i, x in enumerate(plan.get("external", []) or []):
        xid = str(x.get("id", ""))
        if not AGENT_ID.match(xid):
            ctx.err(f"plan.external[{i}].id: `{xid}` is not a lowercase id")
        if xid in ctx.agents:
            ctx.err(f"plan.external[{i}].id: `{xid}` is already recorded — one id per agent or source")
        if not norm(x.get("report", "")):
            ctx.err(f"plan.external[{i}].report: where the source's report lives — its findings cite it")
        ctx.agents[xid] = EXTERNAL
    if budget and launched > budget:
        ctx.err(f"budget: {launched} agents launched, {budget} approved — stop and ask before the next one")
    return budget


def fingerprint_index(ctx: Ctx, findings: list) -> dict:
    by_fp: dict = {}
    for i, f in enumerate(findings):
        fp = str(f.get("fingerprint", ""))
        if fp in by_fp:
            ctx.err(f"findings[{i}]: fingerprint `{fp}` appears twice")
        by_fp[fp] = f
    return by_fp


def unit_errors(ctx: Ctx, u: dict, where: str, by_fp: dict) -> set[str]:
    """Checks one unit against the state table; returns the fingerprints it links."""
    status, cls = str(u.get("status", "")), str(u.get("class", ""))
    if cls not in ctx.cards:
        ctx.err(f"{where}.class: `{cls}` is not a card in the catalogue")
    if not norm(u.get("boundary", "")):
        ctx.err(f"{where}.boundary: name the threat-model boundary this unit tests")
    if status not in UNIT_STATES:
        ctx.err(f"{where}.status: `{status}` is not a unit state")
        return set()
    finder = ctx.agents.get(str(u.get("agent")))
    if status == "in_progress" and finder != "hunter":
        ctx.err(f"{where}.agent: an in_progress unit names the hunter recorded in plan.agents")
    elif status in ("covered", "candidate") and finder not in FINDERS:
        ctx.err(f"{where}.agent: a {status} unit names the hunter in plan.agents or the source in plan.external")
    if status in ("covered", "candidate"):
        paths = u.get("reviewed_paths") or []
        if not paths:
            ctx.err(f"{where}.reviewed_paths: a {status} unit lists what the hunter read")
        for p in (p for p in paths if inside(ctx.repo, p) is None or not inside(ctx.repo, p).exists()):
            ctx.err(f"{where}.reviewed_paths: `{p}` does not exist")
    if "raised_by" in u and ctx.agents.get(str(u.get("raised_by"))) != "critic":
        ctx.err(f"{where}.raised_by: `{u.get('raised_by')}` is not a critic recorded in plan.agents")
    if status in ("blocked", "deferred", "out_of_scope") and not norm(u.get("note", "")):
        ctx.err(f"{where}.note: say why the unit is {status}")
    coverage_errors(ctx, u, where)
    if status != "candidate":
        return set()
    fps = u.get("fingerprints") or []
    if not fps:
        ctx.err(f"{where}.fingerprints: a candidate unit names its findings")
    for fp in (fp for fp in fps if fp not in by_fp):
        ctx.err(f"{where}.fingerprints: `{fp}` is not in findings.json")
    return set(fps)


def coverage_errors(ctx: Ctx, u: dict, where: str) -> None:
    """`covered_at` and `card_sha` are optional (older ledgers lack them; `stale` reports
    those units as unknown), but when present they name a real commit and a card hash."""
    if "covered_at" in u and not commit_of(ctx.repo, str(u.get("covered_at"))):
        ctx.err(f"{where}.covered_at: `{u.get('covered_at')}` is not a commit HEAD descends from "
                "— the HEAD the hunter read")
    if "card_sha" in u and not re.fullmatch(r"[0-9a-f]{64}", str(u.get("card_sha"))):
        ctx.err(f"{where}.card_sha: the sha256 of the class card, 64 hex characters")


def finding_errors(ctx: Ctx, f: dict, where: str) -> None:
    cls, state = str(f.get("class", "")), str(f.get("state", ""))
    if cls not in ctx.cards:
        ctx.err(f"{where}.class: `{cls}` is not a card in the catalogue")
    elif f.get("check") != ctx.cards[cls]:
        ctx.err(f"{where}.check: class {cls} fails `{ctx.cards[cls]}`, not `{f.get('check')}`")
    if state not in FINDING_STATES:
        ctx.err(f"{where}.state: `{state}` is not a finding state")
    trace_errors(ctx, f, where)
    claim = f.get("claim") or {}
    for k in (k for k in CLAIM_FIELDS if not norm(claim.get(k, ""))):
        ctx.err(f"{where}.claim.{k}: a candidate names {k} — without it there is no boundary to cross")
    if ctx.agents.get(str(f.get("found_by"))) not in FINDERS:
        ctx.err(f"{where}.found_by: the hunter recorded in plan.agents, or the source in plan.external")
    # Independence is structural: an id has one role, so the hunter that found a
    # candidate can never be the verifier that settles it. A finding fixed by an
    # adopted regression test may have had none: the person accepted the claim by
    # fixing it, and the test, not an agent, is what holds it closed.
    adopted = state == "fixed" and (f.get("proof") or {}).get("kind") == "regression"
    verifier = f.get("verified_by")
    if adopted and verifier is None:
        pass
    elif state != "candidate" and ctx.agents.get(str(verifier)) != "verifier":
        ctx.err(f"{where}.verified_by: a {state} finding names a verifier recorded in plan.agents "
                "— never the hunter that found it")
    state_errors(ctx, f, where, state)


def trace_errors(ctx: Ctx, f: dict, where: str) -> None:
    trace = f.get("trace") or []
    if not trace:
        ctx.err(f"{where}.trace: a finding names the path from entry to sink")
        return
    if str(trace[-1].get("kind")) != "sink":
        ctx.err(f"{where}.trace: the last step is the sink")
    if len(trace) > 1 and str(trace[0].get("kind")) != "entry":
        ctx.err(f"{where}.trace: the first step is the entry")
    # The fix changed the code the trace cites, so a fixed finding's trace is held
    # to the commit it was found at; every other state is held to the working tree.
    at = ""
    if f.get("state") == "fixed":
        at = commit_of(ctx.repo, str(f.get("found_at", "")))
        if not at:
            ctx.err(f"{where}.found_at: `{f.get('found_at')}` is not a commit HEAD descends from "
                    "— a fixed finding names the commit its trace was read at")
            return
    for j, step in enumerate(trace):
        why = resolve_step(ctx.repo, step, at)
        if why:
            ctx.err(f"{where}.trace[{j}]: {why}")
    expected = fingerprint(str(f.get("class", "")), trace[-1])
    if f.get("fingerprint") != expected:
        ctx.err(f"{where}.fingerprint: expected `{expected}` (class @ sink path # sink excerpt)")


def state_errors(ctx: Ctx, f: dict, where: str, state: str) -> None:
    sev = f.get("severity")
    if state in ("candidate", "needs_validation", "rejected") and sev:
        ctx.err(f"{where}.severity: only a proven finding carries one — a {state} has none")
    if state == "confirmed":
        if sev not in SEVERITIES:
            ctx.err(f"{where}.severity: one of {', '.join(SEVERITIES)}")
        if sev in NEEDS_IMPACT and not norm(f.get("impact", "")):
            ctx.err(f"{where}.impact: required at {sev} — who loses what")
        if not norm(f.get("fix", "")):
            ctx.err(f"{where}.fix: the smallest change that restores the invariant")
        proof_errors(ctx, f, where, "red")
    if state == "fixed":
        proof_errors(ctx, f, where, "held")
    missing = [k for k in ("missing_fact", "validation_plan") if not norm(f.get(k, ""))]
    if state == "needs_validation" and missing:
        ctx.err(f"{where}.{missing[0]}: required — the fact the repo cannot show, and how its owner checks it")
    if state == "rejected" and not norm(f.get("reason", "")):
        ctx.err(f"{where}.reason: why the claim fails (the control that held, cited)")


def proof_errors(ctx: Ctx, f: dict, where: str, want: str) -> None:
    p = f.get("proof") or {}
    if p.get("outcome") != want:
        ctx.err(f"{where}.proof: outcome is `{p.get('outcome')}`, a {f.get('state')} finding needs `{want}` "
                "— run `hunt.py prove`")
        return
    if ctx.head and p.get("head") != ctx.head:
        ctx.err(f"{where}.proof: ran at {str(p.get('head'))[:12]}, HEAD is {ctx.head[:12]} — run `hunt.py reprove`")
    why = log_error(ctx.repo, p)
    if why:
        ctx.err(f"{where}.proof.{why.replace('`hunt.py`', '`hunt.py prove`')}")
    if p.get("kind") == "regression":
        why = regression_refusal(ctx.repo, str(p.get("test_path", "")), str(p.get("command", "")), clean=False)
        if why:
            ctx.err(f"{where}.proof: {why}")
        baseline_errors(ctx, f, where)


def baseline_errors(ctx: Ctx, f: dict, where: str) -> None:
    """A regression test's run on the unfixed code. A ledger adopted before baselines
    existed has none: `summary.baselines.missing` counts it, `rebaseline` settles it."""
    b = (f.get("proof") or {}).get("baseline")
    if b is None:
        return
    outcome = b.get("outcome")
    if outcome not in BASELINES:
        ctx.err(f"{where}.proof.baseline.outcome: `{outcome}` is not {', '.join(sorted(BASELINES))}")
    elif outcome == "held":
        ctx.err(f"{where}.proof.baseline: the regression test passes on the unfixed code at "
                f"{str(b.get('commit'))[:12]} — it proves nothing; adopt a test that fails there")
    elif outcome == "unproven" and not norm(b.get("reason", "")):
        ctx.err(f"{where}.proof.baseline.reason: why the test could not run on the unfixed code")
    if outcome in ("red", "held") and b.get("commit") != commit_of(ctx.repo, str(f.get("found_at", ""))):
        ctx.err(f"{where}.proof.baseline: ran at {str(b.get('commit'))[:12]}, not at found_at — run `hunt.py rebaseline`")
    if outcome == "red" and log_error(ctx.repo, b):
        ctx.err(f"{where}.proof.baseline.{log_error(ctx.repo, b)}")


def summarise(ctx: Ctx, units: list, findings: list, budget: int) -> dict:
    def count(items: list, key: str) -> dict:
        return {s: sum(1 for x in items if str(x.get(key)) == s) for s in sorted({str(x.get(key)) for x in items})}
    roles = list(ctx.agents.values())
    return {"head": ctx.head,
            "agents": {"launched": sum(1 for r in roles if r in ROLES), "budget": budget,
                       "external": roles.count(EXTERNAL),
                       "hunters": roles.count("hunter"), "verifiers": roles.count("verifier"),
                       "critics": roles.count("critic")},
            "units": count(units, "status"), "findings": count(findings, "state"),
            "baselines": baseline_counts(findings)}


def baseline_outcome(f: dict) -> str:
    """How a fixed finding's test was seen on the unfixed code. A finding fixed by
    `reprove` ran its own proof red there before it held: that run is its baseline."""
    p = f.get("proof") or {}
    if p.get("kind") != "regression":
        return "red"
    return str((p.get("baseline") or {}).get("outcome") or "missing")


def baseline_counts(findings: list) -> dict:
    fixed = [baseline_outcome(f) for f in findings if f.get("state") == "fixed"]
    return {k: fixed.count(k) for k in ("red", "unproven", "skipped", "missing", "held") if fixed.count(k)}


# ------------------------------------------------------------------ prove

def proof_request(repo: Path, f: dict) -> tuple[dict | None, dict]:
    """The proof's source, destination, command and expected message — or why it cannot run."""
    p = f.get("proof") or {}
    src, dest = inside(repo, str(p.get("file", ""))), inside(repo, str(p.get("test_path", "")))
    command, expect = str(p.get("command", "")).strip(), norm(p.get("failure_excerpt", ""))
    refusal = ""
    if src is None or not src.is_file() or not src.is_relative_to((repo / HUNT / "proofs").resolve()):
        refusal = f"proof.file must be a file under {HUNT.as_posix()}/proofs/"
    elif dest is None or dest.is_relative_to((repo / ".audit").resolve()):
        refusal = "proof.test_path: where the project's runner finds tests, inside the repo"
    elif dest.exists():
        refusal = f"proof.test_path `{p.get('test_path')}` exists — never overwrite a file"
    elif not dest.parent.is_dir():
        refusal = "proof.test_path: its folder does not exist — use the project's test folder"
    elif not command or dest.name not in command:
        refusal = "proof.command must run the proof file by name, not the whole suite"
    elif not expect:
        refusal = "proof.failure_excerpt: the assertion message the red run prints"
    if refusal:
        return None, {"error": refusal}
    dirty = dirty_cited(repo, f)
    if dirty:
        return None, {"error": "cited files have uncommitted changes — the proof would not be of HEAD",
                      "dirty": dirty}
    return {"src": src, "dest": dest, "command": command, "expect": expect}, {}


def run_proof(repo: Path, req: dict) -> tuple[str, int]:
    """Copies the proof in, runs its command, and always removes it again."""
    shutil.copyfile(req["src"], req["dest"])
    try:
        return run_command(repo, req["command"])
    finally:
        req["dest"].unlink(missing_ok=True)


def prove(repo: Path, fp: str) -> tuple[bool, dict]:
    path = repo / HUNT / "findings.json"
    findings = load(path, [])
    f = next((x for x in findings if x.get("fingerprint") == fp), None)
    if f is None:
        return False, {"error": f"no finding `{fp}`"}
    p = f.get("proof") or {}
    if p.get("kind") == "regression":
        # An adopted test runs where it lives. It asserts the fixed behaviour, so a
        # failure is not the claim's red — it is a regression or a broken test, and
        # a verifier tells which.
        refusal = regression_refusal(repo, str(p.get("test_path", "")), str(p.get("command", "")))
        if refusal:
            return False, {"error": refusal}
        output, exit_code = run_command(repo, p["command"])
        outcome = "held" if exit_code == 0 else "broken"
        f["proof"] = {**p, "outcome": outcome,
                      **write_log(repo, f"{slug(fp)}.regression", p["command"], (output, exit_code))}
    else:
        req, refusal = proof_request(repo, f)
        if req is None:
            return False, refusal
        output, exit_code = run_proof(repo, req)
        outcome = outcome_of(exit_code, output, req["expect"])
        f["proof"] = {**p, "outcome": outcome, **write_log(repo, slug(fp), req["command"], (output, exit_code))}
    save(path, findings)
    return True, {"fingerprint": fp, "outcome": outcome, "exit": exit_code, "log": f["proof"]["log"]}


def reprove(repo: Path) -> tuple[bool, dict]:
    path = repo / HUNT / "findings.json"
    results, red_at = [], {}
    for f in load(path, []):
        p = f.get("proof") or {}
        if f.get("state") not in ("confirmed", "fixed") or not (p.get("file") or p.get("kind") == "regression"):
            continue
        if f.get("state") == "confirmed" and p.get("outcome") == "red":
            red_at[f["fingerprint"]] = p.get("head", "")
        ok, r = prove(repo, f["fingerprint"])
        results.append(r)
    # prove() rewrote the file; apply the transitions on the fresh copy.
    findings = load(path, [])
    for f in findings:
        out = (f.get("proof") or {}).get("outcome")
        if f.get("state") == "confirmed" and out == "held":
            f["state"] = "fixed"
            # The trace was read where the proof last ran red; the fix moved the code since.
            f.setdefault("found_at", red_at.get(f["fingerprint"]) or head_of(repo))
        elif f.get("state") == "fixed" and out == "red":
            f["state"] = "confirmed"
    save(path, findings)
    broken = [r for r in results if r.get("outcome") == "broken" or "error" in r]
    return not broken, {"reproved": results, "need_a_verifier": [r.get("fingerprint") for r in broken]}


# ------------------------------------------------------------------ adopt

ADOPTABLE = {"candidate", "confirmed", "needs_validation", "fixed"}


@dataclass
class Adoption:
    """What `adopt` is given: the project's regression test, the command that runs it
    by name, the commit the finding's trace was read at, and how the baseline runs
    there (`setup` prepares that tree; `skip` is the person's explicit escape)."""
    test_path: str
    command: str
    found_at: str = ""
    setup: str = ""
    expect: str = ""
    skip: bool = False


def adopt(repo: Path, fp: str, a: Adoption) -> tuple[bool, dict]:
    """Marks a finding fixed on the strength of a regression test the project keeps.

    The hunt's own proof builds the attack along the path the fix closed, so after
    the fix it turns `broken`, not `held`; and a candidate fixed before any verifier
    ran has no proof at all. The project's regression test is the lasting proof: it
    runs where it lives, and `reprove` runs it again on every hunt. It counts only
    if it also fails on the unfixed code — the baseline, run at `found_at`.
    """
    path = repo / HUNT / "findings.json"
    findings = load(path, [])
    f = next((x for x in findings if x.get("fingerprint") == fp), None)
    at, refusal = adoption_refusal(repo, f, fp, a)
    if refusal:
        return False, refusal
    rel = inside(repo, a.test_path).relative_to(repo).as_posix()
    result = run_command(repo, a.command)
    if result[1] != 0:
        run = write_log(repo, f"{slug(fp)}.regression", a.command, result)
        return False, {"error": "the regression test does not pass on HEAD — nothing adopted",
                       "exit": run["exit"], "log": run["log"]}
    if a.skip:
        baseline = {"outcome": "skipped", "commit": at, "reason": "--no-baseline"}
    else:
        baseline = baseline_record(repo, fp, Baseline(rel, a.command, at, a.setup, a.expect))
    if baseline["outcome"] == "held":
        return False, held_refusal(baseline)
    old = f.get("proof")
    if old and old.get("kind") != "regression":
        f.setdefault("superseded_proofs", []).append(old)
    run = write_log(repo, f"{slug(fp)}.regression", a.command, result)
    f["proof"] = {"kind": "regression", "test_path": rel, "command": a.command, "outcome": "held", **run,
                  "baseline": baseline}
    f["state"], f["found_at"] = "fixed", at
    save(path, findings)
    return True, {"fingerprint": fp, "state": "fixed", "found_at": at, "log": run["log"],
                  "baseline": baseline}


def adoption_refusal(repo: Path, f: dict | None, fp: str, a: Adoption) -> tuple[str, dict]:
    """(the found_at commit, {}) when the finding can be adopted; else ('', the refusal)."""
    if f is None:
        return "", {"error": f"no finding `{fp}`"}
    if f.get("state") not in ADOPTABLE:
        return "", {"error": f"a {f.get('state')} finding cannot be adopted — its claim did not hold"}
    at = commit_of(repo, a.found_at or str(f.get("found_at", "")))
    if not at:
        return "", {"error": "--found-at: the commit the trace was read at, which HEAD descends from"}
    if at == head_of(repo):
        return "", {"error": "--found-at is HEAD — adopt a fix after it is committed, not before"}
    stale_steps = [w for w in (resolve_step(repo, s, at) for s in f.get("trace") or []) if w]
    if stale_steps:
        return "", {"error": f"the trace does not hold at {at[:12]} — the claim is not of that commit",
                    "trace": stale_steps}
    refusal = regression_refusal(repo, a.test_path, a.command)
    return (at, {}) if not refusal else ("", {"error": refusal})


# ------------------------------------------------------------------ emit

def q(s) -> str:
    return '"' + str(s).replace("\\", "/").replace('"', "'").replace("\n", " ")[:300] + '"'


def emit(repo: Path) -> tuple[bool, dict]:
    report = check(repo)
    if not report["ok"]:
        return False, {"error": "the ledger is invalid; fix it before emitting", "errors": report["errors"]}
    target_dir = repo / ".audit" / OWNER
    removed = []
    for old in sorted(target_dir.glob(f"{PRODUCER}--*.evidence.yaml")):
        old.unlink()
        removed.append(old.relative_to(repo).as_posix())
    findings = load(repo / HUNT / "findings.json", [])
    groups: dict[str, list[dict]] = {}
    for f in (f for f in findings if f.get("state") == "confirmed"):
        groups.setdefault(f["check"], []).append(f)
    written = []
    for chk, items in sorted(groups.items()):
        target = target_dir / f"{PRODUCER}--{chk}.evidence.yaml"
        target.parent.mkdir(parents=True, exist_ok=True)
        lines = evidence(chk, items, report["summary"]["head"])
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(target.relative_to(repo).as_posix())
    return True, {"written": written, "removed": removed, **unproven_fixes(findings)}


def unproven_fixes(findings: list) -> dict:
    """The fixed findings no test was seen failing on the unfixed code for: the report
    says so, because their `fixed` rests on a test that may pass on both commits."""
    weak = [f["fingerprint"] for f in findings if f.get("state") == "fixed" and baseline_outcome(f) != "red"]
    if not weak:
        return {"baselines": baseline_counts(findings)}
    return {"baselines": baseline_counts(findings), "unproven_fixes": weak,
            "note": f"{len(weak)} fixed finding(s) rest on a regression test never seen failing on the unfixed "
                    "code (baseline unproven, skipped or missing) — say so in the report; "
                    "`hunt.py rebaseline` runs it"}


def evidence(chk: str, items: list, head: str) -> list[str]:
    """The lines of one FAIL evidence file: the check's confirmed findings, worst first."""
    items.sort(key=lambda x: SEVERITIES.index(x["severity"]))
    top = items[0]
    out = [f"check: {chk}", f"owner: {OWNER}", f"producer: {PRODUCER}", f"instrument: {INSTRUMENT}",
           f"rule: {q(f'{RULE_VERSION} {CHECK_RULE[chk]}')}", f"rule-version: {q(RULE_VERSION)}",
           "methods:", f"  - {INSTRUMENT}", "evidence:"]
    for f in items:
        sink = f["trace"][-1]
        out += [f"  - path: {q(str(sink['path']) + ':' + str(sink['line']))}",
                f"    excerpt: {q(norm(sink['excerpt']))}", "    kind: source",
                f"  - path: {q(f['proof']['log'])}", "    kind: log", f"    hash: {f['proof']['log_sha256']}"]
    return out + ["result: FAIL", f"severity: {top['severity']}", "confidence: OBSERVED",
                  f"command: {q('hunt.py prove ' + top['fingerprint'])}", f"log: {top['proof']['log']}",
                  f"title: {q('; '.join(norm(x['claim']['result']) for x in items))}",
                  f"impact: {q(' | '.join(norm(x.get('impact') or x['claim']['affected']) for x in items))}",
                  f"fix: {q(' | '.join(norm(x['fix']) for x in items))}",
                  "context:", f"  head: {head or 'unknown'}", f"  captured-at: {now()}",
                  f"  findings: {q(', '.join(x['fingerprint'] for x in items))}"]


# ------------------------------------------------------------------ main

def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("action", choices=("check", "record", "stale", "prove", "reprove", "adopt", "rebaseline", "emit"))
    ap.add_argument("fingerprint", nargs="?", help="the finding; record: the agent id")
    ap.add_argument("test_path", nargs="?", help="adopt: the project's regression test; record: the answer file")
    ap.add_argument("--command", default="", help="adopt: runs the regression test by name")
    ap.add_argument("--found-at", default="", help="adopt: the commit the trace was read at")
    ap.add_argument("--baseline-setup", default="", help="adopt, rebaseline: prepares the found_at tree")
    ap.add_argument("--expect", default="", help="adopt, rebaseline: the message the unfixed run prints")
    ap.add_argument("--no-baseline", action="store_true", help="adopt: record the baseline as skipped")
    ap.add_argument("--plan", action="store_true", help="record (critic): raise zones as planned, not deferred")
    ap.add_argument("--repo", default=".")
    return ap


NEEDS = {"prove": ("fingerprint",), "adopt": ("fingerprint", "test_path", "command"),
         "record": ("fingerprint", "test_path")}


def dispatch(a: argparse.Namespace, repo: Path) -> tuple[bool, dict]:
    if a.action == "check":
        out = check(repo)
        return out["ok"], out
    actions = {
        "record": lambda: record(repo, Answer(a.fingerprint, a.test_path, a.plan)),
        "stale": lambda: stale(repo),
        "prove": lambda: prove(repo, a.fingerprint),
        "reprove": lambda: reprove(repo),
        "adopt": lambda: adopt(repo, a.fingerprint, Adoption(a.test_path, a.command, a.found_at,
                                                             a.baseline_setup, a.expect, a.no_baseline)),
        "rebaseline": lambda: rebaseline(repo, Rebaseline(a.fingerprint or "", a.baseline_setup, a.expect)),
        "emit": lambda: emit(repo),
    }
    return actions[a.action]()


def main(argv: list[str] | None = None) -> int:
    ap = parser()
    a = ap.parse_args(argv)
    missing = [n for n in NEEDS.get(a.action, ()) if not getattr(a, n)]
    if missing:
        ap.error(f"{a.action} needs {', '.join(missing)}")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    ok, out = dispatch(a, Path(a.repo).resolve())
    print(json.dumps(out, indent=2, ensure_ascii=False))
    errs = out.get("errors") or ([out["error"]] if "error" in out else [])
    print(f"  {'OK' if ok else 'REFUSED'} {a.action}" + (f" — {len(errs)} error(s); first: {errs[0]}" if errs else ""),
          file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
