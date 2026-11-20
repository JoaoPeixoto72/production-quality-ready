"""hunt_record.py — an agent's answer into the ledger, and which coverage went stale.

`record` writes what a hunter or the critic answered (references/agents.md) so the
parent copies nothing by hand: every excerpt is re-read at its line before a word is
written, and an answer that does not hold is refused whole, the ledger untouched.
`stale` says which covered units must be hunted again: the code they read changed
since `covered_at`, their card changed since `card_sha`, or nobody recorded either.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from hunt_core import CLAIM_FIELDS, FINDERS, HUNT, card_shas, catalogue, commit_of, dirty_cited, \
    fingerprint, git, head_of, inside, load, norm, resolve_step, save

HUNTER_STATES = {"covered", "candidate", "blocked"}


@dataclass
class Ledger:
    """The two files of the hunt, loaded once, and the HEAD the answer was read at."""
    repo: Path
    plan: dict
    findings: list
    head: str
    out: dict = field(default_factory=dict)

    def unit(self, uid: str) -> dict | None:
        return next((u for u in self.plan.get("units", []) or [] if str(u.get("id")) == uid), None)

    def save(self) -> None:
        save(self.repo / HUNT / "plan.json", self.plan)
        save(self.repo / HUNT / "findings.json", self.findings)


@dataclass
class Answer:
    """What `record` is given: the agent recorded in plan.agents, its answer file, and
    whether the critic's zones go to the plan (a hunter will be paid) or are deferred."""
    agent: str
    path: str
    plan: bool = False


def record(repo: Path, a: Answer) -> tuple[bool, dict]:
    plan = load(repo / HUNT / "plan.json", None)
    if plan is None:
        return False, {"error": f"{HUNT.as_posix()}/plan.json missing: plan before hunting"}
    roles = {str(x.get("id")): str(x.get("role")) for x in plan.get("agents", []) or []}
    roles.update({str(x.get("id")): "external" for x in plan.get("external", []) or []})
    role = roles.get(a.agent)
    if role not in FINDERS | {"critic"}:
        return False, {"error": f"`{a.agent}` is not a hunter, critic or external source recorded in the plan "
                                "— record the agent before launching it"}
    try:
        answer = load(Path(a.path), None)
    except ValueError as exc:  # the agent answered something that is not JSON
        return False, {"error": f"{a.path}: not JSON ({exc})"}
    if not isinstance(answer, dict):
        return False, {"error": f"{a.path}: the answer is a JSON object (references/agents.md)"}
    wrong = {"units", "candidates"} & set(answer) if role == "critic" else {"zones"} & set(answer)
    if wrong:
        return False, {"error": f"`{a.agent}` is a {role}; its answer has no `{sorted(wrong)[0]}` "
                                "— a critic raises zones, a hunter answers for units"}
    ledger = Ledger(repo, plan, load(repo / HUNT / "findings.json", []), head_of(repo))
    errors = record_critic(ledger, a, answer) if role == "critic" else record_hunter(ledger, a.agent, answer)
    if errors:
        return False, {"error": f"{len(errors)} problem(s) in the answer — nothing recorded", "errors": errors}
    injection = answer.get("injection") or []
    for item in injection:
        plan.setdefault("injection", []).append({"agent": a.agent, "item": item})
    ledger.save()
    return True, {"agent": a.agent, "role": role, **ledger.out, "injection": injection}


# ------------------------------------------------------------------ hunter

def record_hunter(ledger: Ledger, agent: str, answer: dict) -> list[str]:
    """Checks the whole answer first; writes it only when nothing is refused."""
    units, cands = answer.get("units") or [], answer.get("candidates") or []
    errors = [e for i, u in enumerate(units) for e in hunter_unit_errors(ledger, agent, u, f"units[{i}]")]
    states = {str(u.get("id")): str(u.get("status")) for u in units}
    for i, c in enumerate(cands):
        errors += candidate_errors(ledger, c, f"candidates[{i}]", states)
    for uid in (uid for uid, s in states.items() if s == "candidate"):
        if not any(str(c.get("unit")) == uid for c in cands):
            errors.append(f"units: `{uid}` is a candidate with no candidate in the answer")
    if errors:
        return errors
    shas = card_shas()
    for u in units:
        write_unit(ledger, agent, u, shas)
    cards = catalogue()
    for c in cands:
        write_candidate(ledger, agent, c, cards)
    ledger.out["units"] = [str(u.get("id")) for u in units]
    return []


def hunter_unit_errors(ledger: Ledger, agent: str, u: dict, where: str) -> list[str]:
    uid, status = str(u.get("id", "")), str(u.get("status", ""))
    unit = ledger.unit(uid)
    if unit is None:
        return [f"{where}: unit `{uid}` is not in plan.units — the hunter answers for its own units"]
    errors = []
    if unit.get("agent") not in (None, "", agent):
        errors.append(f"{where}: unit `{uid}` belongs to `{unit.get('agent')}`")
    if status not in HUNTER_STATES:
        errors.append(f"{where}.status: `{status}` is not covered, candidate or blocked")
    paths = u.get("reviewed_paths") or []
    if status in ("covered", "candidate") and not paths:
        errors.append(f"{where}.reviewed_paths: a {status} unit lists what the hunter read")
    for p in paths:
        target = inside(ledger.repo, p)
        if target is None or not target.exists():
            errors.append(f"{where}.reviewed_paths: `{p}` does not exist")
    if status == "blocked" and not norm(u.get("note", "")):
        errors.append(f"{where}.note: say what blocked the unit")
    return errors


def candidate_errors(ledger: Ledger, c: dict, where: str, states: dict) -> list[str]:
    errors = []
    if states.get(str(c.get("unit"))) != "candidate":
        errors.append(f"{where}.unit: `{c.get('unit')}` is not a unit this answer reports as candidate")
    if str(c.get("class")) not in catalogue():
        errors.append(f"{where}.class: `{c.get('class')}` is not a card in the catalogue")
    claim = c.get("claim") or {}
    errors += [f"{where}.claim.{k}: missing — without the six it is not a candidate"
               for k in CLAIM_FIELDS if not norm(claim.get(k, ""))]
    return errors + trace_refusals(ledger, c, where)


def trace_refusals(ledger: Ledger, c: dict, where: str) -> list[str]:
    """The trace as the hunter wrote it: in order, entry first and sink last, each
    excerpt on its cited line of the committed tree. Nothing is reordered or moved."""
    trace = c.get("trace") or []
    if not trace:
        return [f"{where}.trace: a candidate names the path from entry to sink"]
    errors = []
    if str(trace[-1].get("kind")) != "sink":
        errors.append(f"{where}.trace: the last step is `{trace[-1].get('kind')}`, not the sink — "
                      "send the trace back to the hunter, nothing is reordered here")
    if len(trace) > 1 and str(trace[0].get("kind")) != "entry":
        errors.append(f"{where}.trace: the first step is `{trace[0].get('kind')}`, not the entry")
    for j, step in enumerate(trace):
        why = resolve_step(ledger.repo, step)
        if why:
            errors.append(f"{where}.trace[{j}]: {why}")
    dirty = dirty_cited(ledger.repo, c)
    if dirty:
        errors.append(f"{where}.trace: cited files have uncommitted changes ({dirty[0].strip()}) "
                      "— found_at would not be the code the hunter read")
    return errors


def write_unit(ledger: Ledger, agent: str, u: dict, shas: dict) -> None:
    unit = ledger.unit(str(u.get("id")))
    unit.update(status=u["status"], agent=agent, reviewed_paths=list(u.get("reviewed_paths") or []),
                covered_at=ledger.head)
    if str(unit.get("class")) in shas:
        unit["card_sha"] = shas[str(unit.get("class"))]
    if norm(u.get("note", "")):
        unit["note"] = u["note"]


def write_candidate(ledger: Ledger, agent: str, c: dict, cards: dict) -> None:
    fp = fingerprint(str(c["class"]), c["trace"][-1])
    unit = ledger.unit(str(c["unit"]))
    unit["fingerprints"] = sorted(set(unit.get("fingerprints") or []) | {fp})
    if any(f.get("fingerprint") == fp for f in ledger.findings):
        ledger.out.setdefault("findings_linked", []).append(fp)
        return
    ledger.findings.append({"fingerprint": fp, "class": c["class"], "check": cards[c["class"]],
                            "state": "candidate", "found_by": agent, "found_at": ledger.head,
                            "claim": {k: c["claim"][k] for k in CLAIM_FIELDS}, "trace": c["trace"]})
    ledger.out.setdefault("findings_added", []).append(fp)


# ------------------------------------------------------------------ critic

def record_critic(ledger: Ledger, a: Answer, answer: dict) -> list[str]:
    zones, cards = answer.get("zones") or [], catalogue()
    errors = []
    for i, z in enumerate(zones):
        if str(z.get("class")) not in cards:
            errors.append(f"zones[{i}].class: `{z.get('class')}` is not a card in the catalogue")
        errors += [f"zones[{i}].{k}: required" for k in ("boundary", "why") if not norm(z.get(k, ""))]
    if errors:
        return errors
    units = ledger.plan.setdefault("units", [])
    raised = []
    for z in zones:
        uid = next_unit_id(units)
        units.append({"id": uid, "boundary": z["boundary"], "class": z["class"],
                      "status": "planned" if a.plan else "deferred", "raised_by": a.agent,
                      "starting_paths": list(z.get("paths") or []), "note": z["why"]})
        raised.append(uid)
    ledger.out["units_raised"] = raised
    return []


def next_unit_id(units: list) -> str:
    """The next id in the plan's own numbering (U9 → U10, U09 → U10)."""
    numbered = [m for m in (re.match(r"^(.*?)(\d+)$", str(u.get("id", ""))) for u in units) if m]
    if not numbered:
        return f"U{len(units) + 1}"
    prefix, width = numbered[-1].group(1), len(numbered[-1].group(2))
    top = max(int(m.group(2)) for m in numbered if m.group(1) == prefix)
    return f"{prefix}{top + 1:0{width}d}"


# ------------------------------------------------------------------ stale

def stale(repo: Path) -> tuple[bool, dict]:
    plan = load(repo / HUNT / "plan.json", None)
    if plan is None:
        return False, {"error": f"{HUNT.as_posix()}/plan.json missing: plan before hunting"}
    shas, found, fresh = card_shas(), [], []
    for u in plan.get("units", []) or []:
        if u.get("status") not in ("covered", "candidate"):
            continue
        why = stale_reason(repo, u, shas)
        if why:
            found.append({"id": u.get("id"), "boundary": u.get("boundary"), "class": u.get("class"), **why})
        else:
            fresh.append(u.get("id"))
    return True, {"head": head_of(repo), "stale": found, "fresh": fresh}


def stale_reason(repo: Path, u: dict, shas: dict) -> dict:
    """{} when the unit's coverage still describes HEAD; else why it does not."""
    at, paths = commit_of(repo, str(u.get("covered_at", ""))), u.get("reviewed_paths") or []
    if not at or not paths:
        return {"reason": "unknown", "detail": "no covered_at (or not a commit HEAD descends from) "
                                               "or no reviewed_paths — nobody can say what was read where"}
    _, changed = git(repo, "diff", "--name-only", at, "HEAD", "--", *paths)
    reasons, out = [], {}
    if changed:
        reasons.append("code")
        out["changed"] = changed.splitlines()
    if u.get("card_sha") and u.get("card_sha") != shas.get(str(u.get("class"))):
        reasons.append("card")
    return {"reason": "+".join(reasons), "covered_at": at, **out} if reasons else {}
