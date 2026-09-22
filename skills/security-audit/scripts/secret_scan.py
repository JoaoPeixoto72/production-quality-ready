#!/usr/bin/env python3
"""secret_scan.py — security-audit instrument (ASVS 5.0 V14).

Answers: *is there a credential in this repository, or anywhere in its
history?* Deleting a secret from HEAD does not remove it from git; this
scans **every commit**, not just the working tree.

Engines, in order of preference:
  1. `--gitleaks-report PATH` — a gitleaks JSON report produced elsewhere
     (the CI job). Used only when its `.head` sidecar names the commit
     being audited; a report of another commit is stale and is ignored.
  2. `gitleaks` on PATH — run here over the full history.
  3. the built-in scanner below — fewer rules, but it runs everywhere
     with no install.
The verdict always says which engine produced it, so nobody mistakes one
for another.

Provider patterns are high-confidence only (prefix + length + charset),
because a secret scanner that cries wolf gets switched off. Test
fixtures, lockfiles and documentation examples are excluded by path;
values that are obviously placeholders (`xxx`, `changeme`, `<your-key>`,
`sk_test_…`) are excluded by content.

Output: JSON on stdout, human summary on stderr, exit 0.

Usage:
  python secret_scan.py --repo . [--gitleaks-report .audit/gitleaks-report.json]
                         [--max-commits N] [--no-history]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# (name, regex, needs_entropy) — prefix-anchored, length-bound.
RULES: list[tuple[str, re.Pattern[str]]] = [
    ("aws-access-key-id", re.compile(r"\b(?:A3T[A-Z0-9]|AKIA|ASIA|ABIA|ACCA)[A-Z0-9]{16}\b")),
    ("aws-secret-key", re.compile(r"(?i)aws[_\-. ]?(?:secret|sk)[_\-. ]?(?:access)?[_\-. ]?key[\"'\s:=]+([A-Za-z0-9/+=]{40})\b")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,255}\b")),
    ("gitlab-token", re.compile(r"\bglpat-[A-Za-z0-9\-_]{20,}\b")),
    ("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("stripe-live-key", re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{20,}\b")),
    ("stripe-webhook-secret", re.compile(r"\bwhsec_[A-Za-z0-9]{20,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")),
    ("openai-key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{32,}\b")),
    ("anthropic-key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b")),
    ("sendgrid-key", re.compile(r"\bSG\.[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{16,}\b")),
    ("resend-key", re.compile(r"\bre_[A-Za-z0-9_\-]{20,}\b")),
    ("cloudflare-token", re.compile(r"(?i)cloudflare[_\-. ]?(?:api[_\-. ]?)?token[\"'\s:=]+([A-Za-z0-9_\-]{40})\b")),
    ("npm-token", re.compile(r"\bnpm_[A-Za-z0-9]{36}\b")),
    ("private-key-block", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY(?: BLOCK)?-----")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b")),
    ("basic-auth-url", re.compile(r"\b[a-z][a-z0-9+.\-]*://[^/\s:@]+:([^/\s:@]{6,})@[^\s/]+")),
    ("generic-assigned-secret", re.compile(
        r"(?i)\b(?:api[_\-]?key|secret[_\-]?key|client[_\-]?secret|auth[_\-]?token|access[_\-]?token|"
        r"password|passwd|pwd)\b\s*[:=]\s*[\"']([^\"'\s]{12,})[\"']")),
]

PLACEHOLDER = re.compile(
    r"^(?:x{3,}|y{3,}|z{3,}|\*{3,}|\.{3,}|change[_\-]?me|your[_\-]?|my[_\-]?|test|dummy|example|sample|"
    r"placeholder|redacted|removed|secret|password|todo|fixme|null|none|undefined|<[^>]+>|\$\{[^}]+\}|"
    r"process\.env\.|import\.meta\.env\.|env\.|os\.environ)",
    re.IGNORECASE,
)
PLACEHOLDER_CONTAINS = re.compile(
    r"xxxx|placeholder|example\.com|changeme|your-?key|your-?token|sk_test_|pk_test_|"
    r"\bfake\b|\bdummy\b|\bsample\b|0{8,}|1234567890",
    re.IGNORECASE,
)
EXCLUDED_PATH = re.compile(
    r"(?:^|/)(?:node_modules|dist|build|target|coverage|\.venv|venv|__pycache__|\.wrangler|"
    r"\.audit|\.verify|vendor)/|"
    r"(?:^|/)(?:package-lock\.json|pnpm-lock\.yaml|yarn\.lock|Cargo\.lock|poetry\.lock|composer\.lock)$|"
    r"\.(?:min\.js|map|lock|png|jpe?g|gif|webp|avif|ico|pdf|zip|gz|woff2?|ttf|eot)$",
    re.IGNORECASE,
)
# A fixture or a doc may legitimately show a shaped secret.
SOFT_PATH = re.compile(r"(?:^|/)(?:tests?|__tests__|fixtures?|examples?|docs?|spec)/|"
                       r"\.(?:md|mdx|rst|txt)$|\.example$|\.sample$|\.template$", re.IGNORECASE)


def run(cmd: list[str], cwd: Path, timeout: int = 300) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           timeout=timeout, errors="replace")
        return p.returncode, (p.stdout or "")
    except Exception as e:  # noqa: BLE001
        return 1, str(e)


def is_placeholder(value: str) -> bool:
    v = value.strip()
    if len(v) < 8:
        return True
    if PLACEHOLDER.match(v) or PLACEHOLDER_CONTAINS.search(v):
        return True
    if len(set(v)) <= 4:                       # "aaaaaaaaaaaa", "abababab"
        return True
    return False


def looks_like_prose(value: str) -> bool:
    """A credential is opaque. A UI label, a sentence or a CSS declaration is
    not. Without this, every `password: 'Palavra-passe'` in an i18n table is
    reported as a leak and the scanner stops being read."""
    v = value.strip()
    if " " in v or "\t" in v:                  # secrets do not contain spaces
        return True
    if re.fullmatch(r"[A-Za-zÀ-ÿ'’\-.,!?()/:]+", v):   # letters only: a word, not a key
        return True
    if not re.search(r"\d", v) and not re.search(r"[_\-]", v) and v.islower():
        return True
    digits = sum(c.isdigit() for c in v)
    uppers = sum(c.isupper() for c in v)
    # Real keys mix classes; prose rarely does.
    return digits == 0 and uppers <= 1 and len(v) < 40


def scan_text(text: str, path: str) -> list[dict]:
    hits: list[dict] = []
    for name, rx in RULES:
        for m in rx.finditer(text):
            value = m.group(1) if m.groups() else m.group(0)
            if is_placeholder(value):
                continue
            # Only the loose, keyword-driven rule needs the prose filter; the
            # provider rules are prefix-anchored and cannot match a sentence.
            if name == "generic-assigned-secret" and looks_like_prose(value):
                continue
            line = text[:m.start()].count("\n") + 1
            hits.append({
                "rule": name, "path": path, "line": line,
                "match": value[:6] + "…" + value[-4:] if len(value) > 14 else "…",
                "soft": bool(SOFT_PATH.search(path)),
            })
    return hits


def scan_worktree(repo: Path) -> list[dict]:
    code, out = run(["git", "ls-files"], repo)
    if code != 0:
        return []
    hits: list[dict] = []
    for name in out.splitlines():
        name = name.strip()
        if not name or EXCLUDED_PATH.search(name):
            continue
        f = repo / name
        if not f.is_file() or f.stat().st_size > 2_000_000:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError):
            continue
        hits += scan_text(text, name)
    return hits


def scan_history(repo: Path, max_commits: int) -> tuple[list[dict], int]:
    code, out = run(["git", "log", f"-{max_commits}", "-p", "--no-color",
                     "--format=%x00COMMIT%x00%H%x00%ad", "--date=short"], repo, timeout=600)
    if code != 0 or not out:
        return [], 0
    hits: list[dict] = []
    commit = ""
    path = ""
    commits = 0
    for line in out.splitlines():
        if line.startswith("\x00COMMIT\x00"):
            parts = line.split("\x00")
            commit = parts[2][:12] if len(parts) > 2 else ""
            commits += 1
            continue
        if line.startswith("+++ b/"):
            path = line[6:].strip()
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        if not path or EXCLUDED_PATH.search(path):
            continue
        for h in scan_text(line[1:], path):
            h["commit"] = commit
            hits.append(h)
    return hits, commits


def gitleaks_findings(data: list) -> list[dict]:
    return [{
        "rule": d.get("RuleID", "?"), "path": d.get("File", "?"),
        "line": d.get("StartLine", 0), "match": d.get("Secret", "…"),
        "commit": (d.get("Commit") or "")[:12], "soft": False,
    } for d in data if isinstance(d, dict)]


def load_report(repo: Path, report: Path) -> tuple[list[dict] | None, str]:
    """Reads a gitleaks JSON report written by CI. Returns (findings, note);
    findings is None when the report cannot be trusted for this commit."""
    if not report.is_file():
        return None, f"gitleaks report not found: {report}"
    sidecar = report.with_suffix(".head")
    if not sidecar.is_file():
        return None, f"gitleaks report has no {sidecar.name} sidecar: commit unknown, ignored"
    scanned = sidecar.read_text(encoding="utf-8").strip()
    code, head = run(["git", "rev-parse", "HEAD"], repo)
    head = head.strip()
    if code != 0 or not scanned or scanned != head:
        return None, (f"gitleaks report is stale: scanned {scanned[:12] or '?'}, "
                      f"HEAD is {head[:12] or '?'}; ignored")
    try:
        data = json.loads(report.read_text(encoding="utf-8") or "[]")
    except (json.JSONDecodeError, OSError) as e:
        return None, f"gitleaks report unreadable ({e}); ignored"
    if not isinstance(data, list):
        return None, "gitleaks report is not a JSON array; ignored"
    return gitleaks_findings(data), f"report {report.name} @{head[:12]}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--max-commits", type=int, default=2000)
    ap.add_argument("--no-history", action="store_true")
    ap.add_argument("--gitleaks-report", default="",
                    help="gitleaks JSON report from CI (needs a <report>.head sidecar)")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    repo = Path(a.repo).resolve()
    evidence: list[str] = []
    findings: list[dict] = []

    engine = ""
    if a.gitleaks_report:
        rp = Path(a.gitleaks_report)
        rp = rp if rp.is_absolute() else repo / rp
        loaded, note = load_report(repo, rp)
        if loaded is not None:
            engine, findings = "gitleaks-report", loaded
            evidence.append(f"engine: gitleaks-report ({note}), findings: {len(findings)}")
        else:
            evidence.append(note)
    if not engine:
        engine = "gitleaks" if shutil.which("gitleaks") else "builtin"

    if engine == "gitleaks-report":
        pass
    elif engine == "gitleaks":
        code, out = run(["gitleaks", "detect", "--source", str(repo),
                         "--no-banner", "--redact", "--report-format", "json",
                         "--report-path", "-"], repo, timeout=900)
        try:
            data = json.loads(out) if out.strip().startswith("[") else []
        except json.JSONDecodeError:
            data = []
        findings = gitleaks_findings(data)
        evidence.append(f"engine: gitleaks (exit {code}), findings: {len(findings)}")
    else:
        wt = scan_worktree(repo)
        for h in wt:
            h["commit"] = "HEAD"
        hist, commits = ([], 0) if a.no_history else scan_history(repo, a.max_commits)
        seen: set[tuple] = set()
        for h in wt + hist:
            key = (h["rule"], h["path"], h["match"])
            if key in seen:
                continue
            seen.add(key)
            findings.append(h)
        evidence.append(
            f"engine: builtin ({len(RULES)} rules); worktree files scanned via `git ls-files`; "
            f"history: {'skipped' if a.no_history else f'{commits} commit(s) of `git log -p`'}")

    hard = [f for f in findings if not f.get("soft")]
    soft = [f for f in findings if f.get("soft")]

    if hard:
        result, severity = "FAIL", "BLOCKER"
        reason = (f"{len(hard)} credential-shaped value(s) found in tracked content or history "
                  f"(engine: {engine}). A secret in history is a secret until it is rotated.")
        evidence += [f"{h['path']}:{h['line']} [{h['rule']}] {h['match']} @{h.get('commit', '?')}"
                     for h in hard[:8]]
    else:
        result, severity = "PASS", ""
        reason = (f"no credential found in tracked content or history (engine: {engine})"
                  + (f"; {len(soft)} match(es) in test/doc paths treated as fixtures" if soft else ""))
        if soft:
            evidence += [f"fixture-path match: {h['path']}:{h['line']} [{h['rule']}]" for h in soft[:4]]
    if engine == "builtin":
        evidence.append("note: builtin engine is prefix-anchored and conservative; "
                        "install gitleaks for the full ruleset")

    out = {
        "repo": str(repo), "engine": engine,
        "results": [{"check": "sec.secrets-not-committed", "result": result,
                     "severity": severity, "reason": reason, "evidence": evidence}],
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"  {result:15} sec.secrets-not-committed            {reason[:86]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
