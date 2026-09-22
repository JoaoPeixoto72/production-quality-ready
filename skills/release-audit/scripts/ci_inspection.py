#!/usr/bin/env python3
"""ci_inspection.py — release-audit instrument.

Decides the `release.*` checks that are *readable* from the repository:
the CI workflow, the manifests, the lockfile and the git log. It never
deploys, never builds twice, never signs anything. What it cannot read
it reports as NOT_VERIFIED with the reason, so the gap stays declared.

Each check answers a question a parser can settle:

  release.ci-matrix-declared     which runtimes/platforms does CI test?
  release.changelog-from-git     does a changelog exist and track the
                                 version that is being shipped?
  release.deploy-single-command  is there ONE declared command that
                                 deploys from a clean clone?
  release.rollback-declared      is there a documented way back?
  release.migrations-in-pipeline are schema migrations applied by the
                                 pipeline (or verified there), not by hand?
  release.env-parity             are staging/production the same build
                                 with different configuration?
  release.reproducible-artifact  NOT_VERIFIED here by construction — it
                                 needs two clean builds; reported so the
                                 owner knows the instrument is missing.

Output: JSON on stdout (list of {check, result, severity, reason,
evidence:[...]}) plus a human summary on stderr. Exit 0 always — the
verdict lives in the JSON, not in the exit code; the caller writes the
evidence files.

Usage:
  python ci_inspection.py --repo . [--platform web|desktop|both]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

CI_GLOBS = (
    ".github/workflows/*.yml", ".github/workflows/*.yaml",
    ".gitlab-ci.yml", "azure-pipelines.yml", ".circleci/config.yml",
    "Jenkinsfile", ".woodpecker.yml", "bitbucket-pipelines.yml",
)
CHANGELOG_NAMES = ("CHANGELOG.md", "CHANGELOG", "CHANGES.md", "HISTORY.md", "NEWS.md")
ROLLBACK_HINT = re.compile(
    r"\broll\s?back\b|\brollback\b|\brevert\b|\bversions?\s+anterior|"
    r"\bwrangler\s+(?:rollback|deployments)\b|\bvercel\s+rollback\b|"
    r"\bkubectl\s+rollout\s+undo\b|\bgit\s+revert\b|\bpromote\b",
    re.IGNORECASE,
)
MIGRATION_CMD = re.compile(
    r"migrat\w*|\bprisma\s+migrate\b|\bdrizzle-kit\b|\bdiesel\s+migration\b|"
    r"\balembic\b|\bflyway\b|\bliquibase\b|\bd1\s+migrations\b",
    re.IGNORECASE,
)
DEPLOY_CMD = re.compile(
    r"\bdeploy\b|\bpublish\b|\bwrangler\s+deploy\b|\bvercel\s+(?:--prod|deploy)\b|"
    r"\bnetlify\s+deploy\b|\bfly\s+deploy\b|\bgh\s+release\b|\bdocker\s+push\b",
    re.IGNORECASE,
)


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=30)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:  # noqa: BLE001 - instrument must not crash the run
        return 1, str(e)


def find_ci_files(repo: Path) -> list[Path]:
    out: list[Path] = []
    for g in CI_GLOBS:
        out.extend(sorted(repo.glob(g)))
    return [p for p in out if p.is_file()]


def rel(p: Path, repo: Path) -> str:
    try:
        return str(p.relative_to(repo)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def load_pkg(repo: Path) -> dict:
    f = repo / "package.json"
    if not f.is_file():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def finding(check: str, result: str, reason: str, evidence: list[str] | None = None,
            severity: str = "") -> dict:
    return {"check": check, "result": result, "severity": severity,
            "reason": reason, "evidence": evidence or []}


# ------------------------------------------------------------------ checks

def check_ci_matrix(repo: Path, ci_files: list[Path]) -> dict:
    if not ci_files:
        return finding("release.ci-matrix-declared", "FAIL",
                       "no CI workflow found (looked for GitHub Actions, GitLab, Azure, CircleCI, Jenkins, Woodpecker, Bitbucket)",
                       severity="HIGH")
    ev: list[str] = []
    runners: set[str] = set()
    versions: set[str] = set()
    for f in ci_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"runs-on:\s*([^\n#]+)", text):
            runners.add(m.group(1).strip().strip("[]"))
        for m in re.finditer(r"(?:node-version|python-version|go-version|toolchain|rust-version):\s*([^\n#]+)", text):
            versions.add(m.group(1).strip())
        if re.search(r"^\s*(?:strategy:|\s+matrix:)", text, re.M):
            ev.append(f"{rel(f, repo)}: matrix block present")
    if runners:
        ev.append("runs-on: " + ", ".join(sorted(runners)))
    if versions:
        ev.append("toolchain: " + ", ".join(sorted(versions)))
    if not runners:
        return finding("release.ci-matrix-declared", "FAIL",
                       "CI exists but declares no runner (`runs-on` or equivalent)",
                       ev, severity="MEDIUM")
    return finding("release.ci-matrix-declared", "PASS",
                   f"{len(ci_files)} CI file(s); the tested platforms/runtimes are declared",
                   ev)


def check_changelog(repo: Path) -> dict:
    ch = next((repo / n for n in CHANGELOG_NAMES if (repo / n).is_file()), None)
    pkg = load_pkg(repo)
    version = str(pkg.get("version") or "").strip()
    if ch is None:
        return finding("release.changelog-from-git", "FAIL",
                       "no changelog file (CHANGELOG.md or equivalent)", severity="MEDIUM")
    text = ch.read_text(encoding="utf-8", errors="replace")
    ev = [f"{rel(ch, repo)}: {len(text.splitlines())} lines"]
    code, out = run(["git", "log", "-1", "--format=%h %ad", "--date=short", "--", ch.name], repo)
    if code == 0 and out.strip():
        ev.append(f"last commit touching it: {out.strip()}")
    if version:
        if version in text:
            ev.append(f"package version {version} appears in the changelog")
            return finding("release.changelog-from-git", "PASS",
                           "changelog exists and covers the version being shipped", ev)
        return finding("release.changelog-from-git", "FAIL",
                       f"changelog exists but does not mention the current version ({version}) — release notes are behind the code",
                       ev, severity="LOW")
    return finding("release.changelog-from-git", "PASS",
                   "changelog exists (no package version to cross-check)", ev)


def check_deploy(repo: Path, pkg: dict, ci_files: list[Path]) -> dict:
    ev: list[str] = []
    scripts = pkg.get("scripts") or {}
    deploy_scripts = {k: v for k, v in scripts.items()
                      if k == "deploy" or k.startswith("deploy:") or DEPLOY_CMD.search(str(v))}
    for k, v in sorted(deploy_scripts.items()):
        ev.append(f"package.json scripts.{k}: {v}")
    for f in ci_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"^\s*run:\s*([^\n]+)$", text, re.M):
            if DEPLOY_CMD.search(m.group(1)):
                ev.append(f"{rel(f, repo)} run: {m.group(1).strip()}")
    if not deploy_scripts and not ev:
        return finding("release.deploy-single-command", "FAIL",
                       "no declared deploy command (no `deploy` script, no deploy step in CI)",
                       severity="HIGH")
    prod = scripts.get("deploy")
    if prod:
        chained = prod.count("&&")
        ev.append(f"steps chained in `deploy`: {chained + 1}")
        return finding("release.deploy-single-command", "PASS",
                       f"one command deploys from a clean clone: `npm run deploy` -> {prod}", ev)
    return finding("release.deploy-single-command", "FAIL",
                   "deploy commands exist but none is the single canonical entry point (`deploy`)",
                   ev, severity="MEDIUM")


def check_rollback(repo: Path, pkg: dict, ci_files: list[Path]) -> dict:
    ev: list[str] = []
    scripts = pkg.get("scripts") or {}
    for k, v in scripts.items():
        if ROLLBACK_HINT.search(k) or ROLLBACK_HINT.search(str(v)):
            ev.append(f"package.json scripts.{k}: {v}")
    docs = [repo / "README.md"] + sorted(repo.glob("docs/**/*.md"))
    for d in docs[:200]:
        if not d.is_file():
            continue
        try:
            text = d.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in ROLLBACK_HINT.finditer(text):
            line = text[:m.start()].count("\n") + 1
            ev.append(f"{rel(d, repo)}:{line}: {text.splitlines()[line-1].strip()[:110]}")
            break
    for f in ci_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        if ROLLBACK_HINT.search(text):
            ev.append(f"{rel(f, repo)}: rollback mentioned in CI")
    if not ev:
        return finding("release.rollback-declared", "FAIL",
                       "no documented way back: no rollback script, no rollback section in README/docs, nothing in CI",
                       severity="HIGH")
    return finding("release.rollback-declared", "PASS",
                   "a rollback path is documented", ev[:6])


def check_migrations_pipeline(repo: Path, pkg: dict, ci_files: list[Path]) -> dict:
    has_migrations = any((repo / d).is_dir() for d in ("migrations", "prisma/migrations", "drizzle", "db/migrate"))
    if not has_migrations:
        return finding("release.migrations-in-pipeline", "NOT_APPLICABLE",
                       "no migrations directory in the repository")
    ev: list[str] = []
    in_ci = False
    for f in ci_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"^\s*(?:-\s*name:\s*([^\n]+)|run:\s*([^\n]+))$", text, re.M):
            line = (m.group(1) or m.group(2) or "").strip()
            if MIGRATION_CMD.search(line):
                ev.append(f"{rel(f, repo)}: {line[:110]}")
                in_ci = True
    scripts = pkg.get("scripts") or {}
    for k, v in scripts.items():
        if MIGRATION_CMD.search(k) or MIGRATION_CMD.search(str(v)):
            ev.append(f"package.json scripts.{k}: {str(v)[:110]}")
    if not in_ci:
        return finding("release.migrations-in-pipeline", "FAIL",
                       "migrations exist but the pipeline neither applies nor verifies them — they are applied by hand",
                       ev, severity="HIGH")
    return finding("release.migrations-in-pipeline", "PASS",
                   "the pipeline applies or verifies schema migrations", ev[:6])


def check_env_parity(repo: Path, pkg: dict, ci_files: list[Path]) -> dict:
    ev: list[str] = []
    envs: set[str] = set()
    wrangler = next((repo / n for n in ("wrangler.jsonc", "wrangler.json", "wrangler.toml") if (repo / n).is_file()), None)
    if wrangler:
        text = wrangler.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'"env"\s*:\s*\{|\[env\.([A-Za-z0-9_-]+)\]|"([A-Za-z0-9_-]+)"\s*:\s*\{[^{}]*"vars"', text):
            name = m.group(1) or m.group(2)
            if name:
                envs.add(name)
        for m in re.finditer(r'^\s*"([a-z0-9_-]+)"\s*:\s*\{', text, re.M):
            pass
        ev.append(f"{rel(wrangler, repo)} present")
    scripts = pkg.get("scripts") or {}
    deploy_like = {k: str(v) for k, v in scripts.items() if k == "deploy" or k.startswith("deploy:")}
    for k, v in sorted(deploy_like.items()):
        ev.append(f"scripts.{k}: {v}")
        m = re.search(r"--env[= ]([A-Za-z0-9_-]+)", v)
        if m:
            envs.add(m.group(1))
    if len(deploy_like) < 2:
        return finding("release.env-parity", "FAIL",
                       "only one deploy target declared: there is no staging built from the same artifact as production",
                       ev, severity="MEDIUM")
    builds = {k: ("npm run build" in v or "build" in v) for k, v in deploy_like.items()}
    if not all(builds.values()):
        return finding("release.env-parity", "FAIL",
                       "deploy targets do not all run the same build step — environments can diverge by more than configuration",
                       ev + [f"build step per target: {builds}"], severity="MEDIUM")
    ev.append(f"environments: {', '.join(sorted(envs)) or 'default + named'}")
    return finding("release.env-parity", "PASS",
                   "staging and production deploy the same build; they differ by configuration only", ev)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--platform", default="web")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    repo = Path(a.repo).resolve()
    ci_files = find_ci_files(repo)
    pkg = load_pkg(repo)

    results = [
        check_ci_matrix(repo, ci_files),
        check_changelog(repo),
        check_deploy(repo, pkg, ci_files),
        check_rollback(repo, pkg, ci_files),
        check_migrations_pipeline(repo, pkg, ci_files),
        check_env_parity(repo, pkg, ci_files),
        finding("release.reproducible-artifact", "NOT_VERIFIED",
                "missing-instrument: needs two clean builds of the same commit on different machines and a hash compare; this instrument only reads the repository"),
    ]

    print(json.dumps({"repo": str(repo), "platform": a.platform,
                      "ci_files": [rel(f, repo) for f in ci_files],
                      "results": results}, indent=2, ensure_ascii=False))
    for r in results:
        print(f"  {r['result']:15} {r['check']:34} {r['reason'][:90]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
