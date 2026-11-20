"""hunt_core.py — what every command of `hunt.py` reads: the ledger's files, git, the
class catalogue, the cited lines, and the run of a test with its pinned log.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
CATALOGUE = HERE.parents[1] / "references" / "classes"
HUNT = Path(".audit") / "security-hunt"
# The critic reads the plan and what the hunters read, once the hunt is done, and names the
# zones nobody looked at. It finds nothing and verifies nothing: it only raises units.
ROLES = {"hunter", "verifier", "critic"}
# An audit run outside the hunt (another tool, a person, a pentest) is recorded in
# `plan.external`. Its findings name it in `found_by`; it costs no agent of the
# budget, and it never settles a finding — a verifier or an adopted test does.
EXTERNAL = "external"
FINDERS = {"hunter", EXTERNAL}
CLAIM_FIELDS = ("principal", "input", "control", "boundary", "affected", "result")
# A run that dies before its assertion is not proof of anything the claim says.
CRASH = re.compile(
    r"SyntaxError|Cannot find module|ModuleNotFoundError|ImportError|No test files found|"
    r"Transform failed|Failed to load|is not defined|TS\d{4}:|command not found|not recognized as",
    re.IGNORECASE)


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


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def cards() -> dict[str, tuple[str, str]]:
    """class id -> (check, the card's text), read from the cards (the cards are the one source)."""
    out: dict[str, tuple[str, str]] = {}
    for f in sorted(CATALOGUE.glob("*.md")):
        for block in re.split(r"(?m)^(?=#{2,3} )", f.read_text(encoding="utf-8")):
            m = re.match(r"### ([a-z0-9][a-z0-9.-]*)\s*\n", block)
            chk = re.search(r"(?m)^- \*\*Check:\*\* `([a-z0-9.-]+)`", block)
            if m and chk:
                out[m.group(1)] = (chk.group(1), block.strip())
    return out


def catalogue() -> dict[str, str]:
    """class id -> check."""
    return {cls: chk for cls, (chk, _) in cards().items()}


def card_shas() -> dict[str, str]:
    """class id -> sha256 of its card's text: a unit covered under an older card is stale."""
    return {cls: hashlib.sha256(text.encode("utf-8")).hexdigest() for cls, (_, text) in cards().items()}


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


def run_command(cwd: Path, command: str) -> tuple[str, int]:
    try:
        run = subprocess.run(command, cwd=cwd, shell=True, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=900)
        return (run.stdout or "") + (run.stderr or ""), run.returncode
    except subprocess.TimeoutExpired:
        return "timeout after 900s", 124


def outcome_of(exit_code: int, output: str, expect: str) -> str:
    if exit_code == 0:
        return "held"
    return "red" if expect in norm(output) and not CRASH.search(output) else "broken"


def pin_log(repo: Path, name: str, text: str) -> dict:
    """Writes proofs/<name>.log; returns the fields that pin it (a later edit fails `check`)."""
    log = repo / HUNT / "proofs" / f"{name}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(text, encoding="utf-8")
    return {"log": log.relative_to(repo).as_posix(), "log_sha256": sha256(log), "ran_at": now()}


def write_log(repo: Path, name: str, command: str, result: tuple[str, int]) -> dict:
    """Writes the run's log as proofs/<name>.log; returns the proof fields that pin it."""
    output, exit_code = result
    pinned = pin_log(repo, name, f"$ {command}\n# exit {exit_code}\n\n{output}")
    return {"exit": exit_code, "head": head_of(repo), **pinned}


def log_error(repo: Path, rec: dict) -> str:
    """'' when the log a record pins is on disk and unchanged."""
    log = inside(repo, str(rec.get("log", "")))
    if log is None or not log.is_file():
        return "log: missing on disk"
    if sha256(log) != rec.get("log_sha256"):
        return "log: changed since `hunt.py` wrote it"
    return ""
