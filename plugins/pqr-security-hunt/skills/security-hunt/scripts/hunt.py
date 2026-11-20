#!/usr/bin/env python3
"""hunt.py — the instrument of `security-hunt`: ledger, proof and evidence.

A hunt is judgement; this script is what keeps the judgement honest. It holds
the run to the repository (every cited line must still say what the claim says),
to its budget (agents launched never exceed the approved number), to
independence (the agent that found a candidate never confirms it), and to proof
(a confirmed finding is a test of the project's own that fails on the current
commit for the reason the claim gives).

    python hunt.py check   [--repo .]
    python hunt.py prove   <fingerprint> [--repo .]
    python hunt.py reprove [--repo .]
    python hunt.py adopt   <fingerprint> <test_path> --command "<cmd>" [--found-at <sha>] [--repo .]
    python hunt.py emit    [--repo .]

Files, all under `<repo>/.audit/security-hunt/` (gitignored with `.audit/`):
  plan.json      scope, budget, agents launched, coverage units
  findings.json  one record per fingerprint
  proofs/        the red tests and their logs

`check`   validates both files against the repo and the class catalogue.
`prove`   copies one proof test into place, runs its command, removes it, and
          records the outcome: red (fails for the stated reason), held (passes:
          the control held), broken (fails for another reason).
`reprove` runs every recorded proof again: re-verification costs no agent.
`adopt`   after a fix: runs a committed regression test of the project and, if it
          passes, marks the finding fixed with that test as its proof; the
          trace is then held to `found_at`, the commit it was read at.
`emit`    writes one FAIL evidence file per `security-audit` check from the
          confirmed findings; it refuses while `check` reports an error.

JSON on stdout, summary on stderr. Exit 0 when the ledger is valid or the action
ran; 1 when it is invalid or the action was refused.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
CATALOGUE = HERE.parents[1] / "references" / "classes"
HUNT = Path(".audit") / "security-hunt"
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
ROLES = {"hunter", "verifier"}
UNIT_STATES = {"planned", "in_progress", "covered", "candidate", "blocked", "deferred", "out_of_scope"}
FINDING_STATES = {"candidate", "confirmed", "needs_validation", "rejected", "fixed"}
CLAIM_FIELDS = ("principal", "input", "control", "boundary", "affected", "result")
AGENT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
# A run that dies before its assertion is not proof of anything the claim says.
CRASH = re.compile(
    r"SyntaxError|Cannot find module|ModuleNotFoundError|ImportError|No test files found|"
    r"Transform failed|Failed to load|is not defined|TS\d{4}:|command not found|not recognized as",
    re.IGNORECASE)


# ------------------------------------------------------------------ helpers

def norm(s: str) -> str:
    return " ".join(str(s).split())


def fingerprint(cls: str, sink: dict) -> str:
    digest = hashlib.sha1(norm(sink.get("excerpt", "")).encode("utf-8")).hexdigest()[:10]
    return f"{cls}@{sink.get('path', '')}#{digest}"


def slug(fp: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", fp).strip("-")[:80]


def git(repo: Path, *args: str, raw: bool = False) -> tuple[int, str]:
    p = subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=repo, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") if raw else (p.stdout or "").strip()


def head_of(repo: Path) -> str:
    code, out = git(repo, "rev-parse", "HEAD")
    return out if code == 0 else ""


def inside(repo: Path, rel: str) -> Path | None:
    """The file a repository-relative path names, or None when it leaves the repo."""
    rel = str(rel).replace("\\", "/")
    if not rel or rel.startswith("/") or re.match(r"^[A-Za-z]:", rel) or ".." in rel.split("/"):
        return None
    p = (repo / rel).resolve()
    return p if p.is_relative_to(repo) else None


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(path: Path, default):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def catalogue() -> dict[str, str]:
    """class id -> check, read from the cards (the cards are the one source)."""
    out: dict[str, str] = {}
    for f in sorted(CATALOGUE.glob("*.md")):
        current = None
        for line in f.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^### ([a-z0-9][a-z0-9.-]*)\s*$", line)
            if m:
                current = m.group(1)
                continue
            m = re.match(r"^- \*\*Check:\*\* `([a-z0-9.-]+)`", line)
            if m and current:
                out[current] = m.group(1)
                current = None
    return out


def commit_of(repo: Path, rev: str) -> str:
    """The full sha `rev` names when it is a commit HEAD descends from; '' otherwise."""
    if not re.match(r"^[0-9a-fA-F]{7,40}$", str(rev or "")):
        return ""
    code, sha = git(repo, "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
    if code != 0 or not sha:
        return ""
    code, _ = git(repo, "merge-base", "--is-ancestor", sha, "HEAD")
    return sha if code == 0 else ""


def resolve_step(repo: Path, step: dict, at: str = "") -> str:
    """'' when the cited line says the excerpt — in the working tree, or at commit
    `at` when given (a fixed finding's trace describes code the fix removed)."""
    path, line, excerpt = step.get("path", ""), step.get("line"), norm(step.get("excerpt", ""))
    target = inside(repo, path)
    if target is None:
        return f"{path}: not a repository-relative path"
    if at:
        code, text = git(repo, "show", f"{at}:{target.relative_to(repo).as_posix()}", raw=True)
        if code != 0:
            return f"{path}: file missing at {at[:12]}"
    elif not target.is_file():
        return f"{path}: file missing"
    else:
        text = target.read_text(encoding="utf-8", errors="replace")
    if len(excerpt) < 6:
        return f"{path}:{line}: excerpt too short to identify a line"
    lines = text.splitlines()
    if isinstance(line, int) and 1 <= line <= len(lines) and excerpt in norm(lines[line - 1]):
        return ""
    moved = [i + 1 for i, text in enumerate(lines) if excerpt in norm(text)]
    if moved:
        return f"{path}:{line}: the excerpt is now at line {moved[0]} — re-read the trace"
    return f"{path}:{line}: the excerpt is not in the file — the claim no longer matches the code"


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
    return {"ok": not ctx.errors, "errors": ctx.errors, "summary": summarise(ctx, units, findings, budget)}


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
            ctx.err(f"plan.agents[{i}].role: `{role}` is not hunter or verifier")
        ctx.agents[aid] = role
    if budget and len(ctx.agents) > budget:
        ctx.err(f"budget: {len(ctx.agents)} agents launched, {budget} approved — stop and ask before the next one")
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
    if status in ("in_progress", "covered", "candidate") and ctx.agents.get(str(u.get("agent"))) != "hunter":
        ctx.err(f"{where}.agent: a {status} unit names the hunter recorded in plan.agents")
    if status in ("covered", "candidate"):
        paths = u.get("reviewed_paths") or []
        if not paths:
            ctx.err(f"{where}.reviewed_paths: a {status} unit lists what the hunter read")
        for p in (p for p in paths if inside(ctx.repo, p) is None or not inside(ctx.repo, p).exists()):
            ctx.err(f"{where}.reviewed_paths: `{p}` does not exist")
    if status in ("blocked", "deferred", "out_of_scope") and not norm(u.get("note", "")):
        ctx.err(f"{where}.note: say why the unit is {status}")
    if status != "candidate":
        return set()
    fps = u.get("fingerprints") or []
    if not fps:
        ctx.err(f"{where}.fingerprints: a candidate unit names its findings")
    for fp in (fp for fp in fps if fp not in by_fp):
        ctx.err(f"{where}.fingerprints: `{fp}` is not in findings.json")
    return set(fps)


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
    if ctx.agents.get(str(f.get("found_by"))) != "hunter":
        ctx.err(f"{where}.found_by: the hunter recorded in plan.agents")
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
    log = inside(ctx.repo, str(p.get("log", "")))
    if log is None or not log.is_file():
        ctx.err(f"{where}.proof.log: missing on disk")
    elif sha256(log) != p.get("log_sha256"):
        ctx.err(f"{where}.proof.log: changed since `hunt.py prove` wrote it")
    if p.get("kind") == "regression":
        why = regression_refusal(ctx.repo, str(p.get("test_path", "")), str(p.get("command", "")), clean=False)
        if why:
            ctx.err(f"{where}.proof: {why}")


def summarise(ctx: Ctx, units: list, findings: list, budget: int) -> dict:
    def count(items: list, key: str) -> dict:
        return {s: sum(1 for x in items if str(x.get(key)) == s) for s in sorted({str(x.get(key)) for x in items})}
    roles = list(ctx.agents.values())
    return {"head": ctx.head,
            "agents": {"launched": len(roles), "budget": budget,
                       "hunters": roles.count("hunter"), "verifiers": roles.count("verifier")},
            "units": count(units, "status"), "findings": count(findings, "state")}


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


def dirty_cited(repo: Path, f: dict) -> list[str]:
    cited = sorted({str(s.get("path")) for s in f.get("trace") or [] if s.get("path")})
    _, dirty = git(repo, "status", "--porcelain", "--", *cited) if cited else (0, "")
    return dirty.splitlines()


def regression_refusal(repo: Path, test_path: str, command: str, clean: bool = True) -> str:
    """'' when `test_path` is a committed test of the project that `command` runs by name."""
    dest = inside(repo, test_path)
    if dest is None or dest.is_relative_to((repo / ".audit").resolve()):
        return "the regression test is a file of the project, inside the repo and outside .audit/"
    if not dest.is_file():
        return f"the regression test `{test_path}` does not exist"
    rel = dest.relative_to(repo).as_posix()
    if git(repo, "ls-files", "--error-unmatch", "--", rel)[0] != 0:
        return f"`{rel}` is not committed — a regression test lives in the project's history"
    # The fix may live in files the trace never cites, so the whole tracked tree
    # must be HEAD — not only the test and the cited lines.
    dirty = git(repo, "status", "--porcelain", "--untracked-files=no")[1] if clean else ""
    if dirty:
        return f"uncommitted changes ({dirty.splitlines()[0].strip()} …) — the run would not be of HEAD"
    if not command.strip() or dest.name not in command:
        return "the command must run the regression test by name, not the whole suite"
    return ""


def run_command(repo: Path, command: str) -> tuple[str, int]:
    try:
        run = subprocess.run(command, cwd=repo, shell=True, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=900)
        return (run.stdout or "") + (run.stderr or ""), run.returncode
    except subprocess.TimeoutExpired:
        return "timeout after 900s", 124


def run_proof(repo: Path, req: dict) -> tuple[str, int]:
    """Copies the proof in, runs its command, and always removes it again."""
    shutil.copyfile(req["src"], req["dest"])
    try:
        return run_command(repo, req["command"])
    finally:
        req["dest"].unlink(missing_ok=True)


def outcome_of(exit_code: int, output: str, expect: str) -> str:
    if exit_code == 0:
        return "held"
    return "red" if expect in norm(output) and not CRASH.search(output) else "broken"


def write_log(repo: Path, name: str, command: str, result: tuple[str, int]) -> dict:
    """Writes the run's log as proofs/<name>.log; returns the proof fields that pin it."""
    output, exit_code = result
    log = repo / HUNT / "proofs" / f"{name}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(f"$ {command}\n# exit {exit_code}\n\n{output}", encoding="utf-8")
    return {"exit": exit_code, "head": head_of(repo), "log": log.relative_to(repo).as_posix(),
            "log_sha256": sha256(log), "ran_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


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
    by name, and the commit the finding's trace was read at."""
    test_path: str
    command: str
    found_at: str = ""


def adopt(repo: Path, fp: str, a: Adoption) -> tuple[bool, dict]:
    """Marks a finding fixed on the strength of a regression test the project keeps.

    The hunt's own proof builds the attack along the path the fix closed, so after
    the fix it turns `broken`, not `held`; and a candidate fixed before any verifier
    ran has no proof at all. The project's regression test is the lasting proof: it
    runs where it lives, and `reprove` runs it again on every hunt.
    """
    path = repo / HUNT / "findings.json"
    findings = load(path, [])
    f = next((x for x in findings if x.get("fingerprint") == fp), None)
    if f is None:
        return False, {"error": f"no finding `{fp}`"}
    if f.get("state") not in ADOPTABLE:
        return False, {"error": f"a {f.get('state')} finding cannot be adopted — its claim did not hold"}
    at = commit_of(repo, a.found_at or str(f.get("found_at", "")))
    if not at:
        return False, {"error": "--found-at: the commit the trace was read at, which HEAD descends from"}
    if at == head_of(repo):
        return False, {"error": "--found-at is HEAD — adopt a fix after it is committed, not before"}
    stale = [w for w in (resolve_step(repo, s, at) for s in f.get("trace") or []) if w]
    if stale:
        return False, {"error": f"the trace does not hold at {at[:12]} — the claim is not of that commit",
                       "trace": stale}
    refusal = regression_refusal(repo, a.test_path, a.command)
    if refusal:
        return False, {"error": refusal}
    rel = inside(repo, a.test_path).relative_to(repo).as_posix()
    run = write_log(repo, f"{slug(fp)}.regression", a.command, run_command(repo, a.command))
    if run["exit"] != 0:
        return False, {"error": "the regression test does not pass on HEAD — nothing adopted",
                       "exit": run["exit"], "log": run["log"]}
    old = f.get("proof")
    if old and old.get("kind") != "regression":
        f.setdefault("superseded_proofs", []).append(old)
    f["proof"] = {"kind": "regression", "test_path": rel, "command": a.command, "outcome": "held", **run}
    f["state"], f["found_at"] = "fixed", at
    save(path, findings)
    return True, {"fingerprint": fp, "state": "fixed", "found_at": at, "log": run["log"]}


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
    groups: dict[str, list[dict]] = {}
    for f in load(repo / HUNT / "findings.json", []):
        if f.get("state") == "confirmed":
            groups.setdefault(f["check"], []).append(f)
    written = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for chk, items in sorted(groups.items()):
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
        out += ["result: FAIL", f"severity: {top['severity']}", "confidence: OBSERVED",
                f"command: {q('hunt.py prove ' + top['fingerprint'])}", f"log: {top['proof']['log']}",
                f"title: {q('; '.join(norm(x['claim']['result']) for x in items))}",
                f"impact: {q(' | '.join(norm(x.get('impact') or x['claim']['affected']) for x in items))}",
                f"fix: {q(' | '.join(norm(x['fix']) for x in items))}",
                "context:", f"  head: {report['summary']['head'] or 'unknown'}", f"  captured-at: {now}",
                f"  findings: {q(', '.join(x['fingerprint'] for x in items))}"]
        target = target_dir / f"{PRODUCER}--{chk}.evidence.yaml"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(out) + "\n", encoding="utf-8")
        written.append(target.relative_to(repo).as_posix())
    return True, {"written": written, "removed": removed}


# ------------------------------------------------------------------ main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("action", choices=("check", "prove", "reprove", "adopt", "emit"))
    ap.add_argument("fingerprint", nargs="?")
    ap.add_argument("test_path", nargs="?", help="adopt: the project's regression test")
    ap.add_argument("--command", default="", help="adopt: runs the regression test by name")
    ap.add_argument("--found-at", default="", help="adopt: the commit the trace was read at")
    ap.add_argument("--repo", default=".")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    repo = Path(a.repo).resolve()

    if a.action == "check":
        out = check(repo)
        ok = out["ok"]
    elif a.action == "prove":
        if not a.fingerprint:
            ap.error("prove needs a fingerprint")
        ok, out = prove(repo, a.fingerprint)
    elif a.action == "reprove":
        ok, out = reprove(repo)
    elif a.action == "adopt":
        if not (a.fingerprint and a.test_path and a.command):
            ap.error("adopt needs a fingerprint, a test path and --command")
        ok, out = adopt(repo, a.fingerprint, Adoption(a.test_path, a.command, a.found_at))
    else:
        ok, out = emit(repo)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    errs = out.get("errors") or ([out["error"]] if "error" in out else [])
    print(f"  {'OK' if ok else 'REFUSED'} {a.action}" + (f" — {len(errs)} error(s); first: {errs[0]}" if errs else ""),
          file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
