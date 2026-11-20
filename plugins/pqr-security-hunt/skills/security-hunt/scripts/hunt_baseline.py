"""hunt_baseline.py — the regression test, run on the code it claims to guard against.

A regression test that passes on HEAD proves nothing unless it also fails on the
unfixed code: a test that passes on both commits closes a finding it never
exercised. The baseline checks out `found_at` in a temporary worktree, copies the
test in as committed at HEAD, runs it there, and keeps the outcome:

  red        it fails at found_at — the test sees the defect the fix removed
  held       it passes at found_at — it proves nothing; `adopt` refuses it
  unproven   setup or compile failure at found_at — nobody saw it fail
  skipped    `--no-baseline`: the person chose not to run it
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from hunt_core import CRASH, HUNT, commit_of, load, norm, outcome_of, pin_log, regression_refusal, \
    run_command, save, slug

BASELINES = {"red", "held", "unproven", "skipped"}


@dataclass
class Baseline:
    """One baseline run: the committed test, the command that runs it by name, the commit
    the finding was read at, and what prepares that commit's tree (an install)."""
    test_path: str
    command: str
    found_at: str
    setup: str = ""
    expect: str = ""


def run_baseline(repo: Path, b: Baseline) -> tuple[dict, str]:
    """(the baseline record, its log text). The worktree is removed whatever happens."""
    tmp = Path(tempfile.mkdtemp(prefix="hunt-baseline-"))
    tree = tmp / "tree"
    try:
        return baseline_in(repo, tree, b)
    finally:
        remove_worktree(repo, tree)
        shutil.rmtree(tmp, ignore_errors=True)


def git_bytes(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=repo, capture_output=True)


def baseline_in(repo: Path, tree: Path, b: Baseline) -> tuple[dict, str]:
    base = {"commit": b.found_at, "test_path": b.test_path, "command": b.command}
    add = git_bytes(repo, "worktree", "add", "--detach", str(tree), b.found_at)
    if add.returncode != 0:
        why = add.stderr.decode("utf-8", "replace").strip()
        return {**base, "outcome": "unproven", "reason": f"git worktree add failed: {why[:200]}"}, why
    test = git_bytes(repo, "show", f"HEAD:{b.test_path}")
    if test.returncode != 0:
        return {**base, "outcome": "unproven", "reason": "the test is not in HEAD"}, ""
    dest = tree / b.test_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(test.stdout)
    log = ""
    if b.setup:
        output, code = run_command(tree, b.setup)
        log = f"$ {b.setup}\n# exit {code}\n\n{output}\n"
        if code != 0:
            return {**base, "outcome": "unproven", "setup": b.setup,
                    "reason": f"--baseline-setup failed at {b.found_at[:12]} (exit {code})"}, log
    output, code = run_command(tree, b.command)
    log += f"$ {b.command}\n# exit {code}\n\n{output}"
    outcome = outcome_of(code, output, norm(b.expect))
    rec = {**base, "outcome": outcome, "exit": code, **({"setup": b.setup} if b.setup else {})}
    if outcome == "broken":
        crash = CRASH.search(output)
        rec.update(outcome="unproven", reason=f"the test could not run at {b.found_at[:12]} (exit {code}"
                   + (f", {crash.group(0)}" if crash else ", not the expected message") + ")")
    return rec, log


def remove_worktree(repo: Path, tree: Path) -> None:
    git_bytes(repo, "worktree", "remove", "--force", str(tree))
    shutil.rmtree(tree, ignore_errors=True)
    git_bytes(repo, "worktree", "prune")


def baseline_record(repo: Path, fp: str, b: Baseline) -> dict:
    """Runs the baseline and pins its log. A `held` run writes beside, never over, the
    log a kept baseline pins: a refused adoption leaves the ledger valid."""
    rec, text = run_baseline(repo, b)
    name = "baseline-held" if rec["outcome"] == "held" else "baseline"
    return {**rec, **pin_log(repo, f"{slug(fp)}.{name}", text or "(no output)\n")}


def held_refusal(rec: dict) -> dict:
    return {"error": f"the regression test passes on the unfixed code at {rec['commit'][:12]} — it proves "
                     "nothing; write one that fails there for the claimed reason", "baseline": rec}


@dataclass
class Rebaseline:
    """What `rebaseline` is given: one fingerprint (or none: every fixed finding without a
    red baseline), the setup of the old tree, and the message the red run prints."""
    fingerprint: str = ""
    setup: str = ""
    expect: str = ""


def rebaseline(repo: Path, r: Rebaseline) -> tuple[bool, dict]:
    """Runs the baseline of already-fixed findings, so a ledger adopted before baselines
    existed learns which of its tests ever saw the defect. States do not change."""
    path = repo / HUNT / "findings.json"
    findings = load(path, [])
    targets = [f for f in findings if f.get("state") == "fixed"
               and (f.get("proof") or {}).get("kind") == "regression"
               and (f.get("fingerprint") == r.fingerprint if r.fingerprint else
                    ((f.get("proof") or {}).get("baseline") or {}).get("outcome") != "red")]
    if r.fingerprint and not targets:
        return False, {"error": f"`{r.fingerprint}` is not a fixed finding adopted by a regression test"}
    results = [rebaseline_one(repo, f, r) for f in targets]
    save(path, findings)
    held = [x["fingerprint"] for x in results if x.get("outcome") == "held"]
    failed = [x for x in results if "error" in x]
    out = {"rebaselined": results, "held": held}
    if held:
        out["error"] = f"{len(held)} regression test(s) pass on the unfixed code — they prove nothing"
    return not held and not failed, out


def rebaseline_one(repo: Path, f: dict, r: Rebaseline) -> dict:
    p, fp = f["proof"], f["fingerprint"]
    at = commit_of(repo, str(f.get("found_at", "")))
    refusal = regression_refusal(repo, str(p.get("test_path", "")), str(p.get("command", "")), clean=False)
    if not at or refusal:
        return {"fingerprint": fp, "error": refusal or "found_at is not a commit HEAD descends from"}
    b = Baseline(str(p["test_path"]), str(p["command"]), at, r.setup, r.expect)
    p["baseline"] = baseline_record(repo, fp, b)
    return {"fingerprint": fp, "outcome": p["baseline"]["outcome"], "log": p["baseline"]["log"],
            **({"reason": p["baseline"]["reason"]} if "reason" in p["baseline"] else {})}
