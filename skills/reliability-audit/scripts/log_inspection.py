#!/usr/bin/env python3
"""log_inspection.py — reliability-audit §2 (diagnosability) instrument.

Answers, by reading the source: *if a customer says "it doesn't work on
version X", what can you find out?*

It is a **static** instrument and says so in every reason string: it
proves the code emits a shape, not that production actually contains it.
Checks that need a captured log sample (`observability.error-diagnosable`
with a real incident) stay NOT_VERIFIED.

Checks decided here:

  observability.logs-structured      logging goes through a helper that
                                     emits JSON/key-value with a level,
                                     not scattered bare console/print
  observability.correlation-id-e2e   one id is attached to log lines and
                                     crosses the request boundary
  observability.pii-redacted         emails/tokens/passwords are not
                                     interpolated into log calls
  observability.retention-declared   retention is written down somewhere
  observability.telemetry-consent    telemetry is opt-in / consent-gated
  observability.version-in-report    version+commit accompany reports
  observability.crash-report-opt-in  desktop only
  observability.error-diagnosable    needs a captured sample -> NOT_VERIFIED

Output: JSON on stdout, human summary on stderr, exit 0.

Usage:
  python log_inspection.py --repo . [--platform web|desktop|both]
                           [--src src] [--docs docs]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CODE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".rs", ".py", ".go", ".java", ".kt", ".swift"}
IGNORED = {".git", "node_modules", "dist", "build", "target", ".venv", "venv",
           "__pycache__", ".wrangler", "coverage", ".audit", ".verify", ".agents"}

BARE_LOG = re.compile(r"(?<![\w.])(?:console\.(?:log|error|warn|info|debug)|print|println!|fmt\.Print\w*)\s*\(")
JSON_IN_LOG = re.compile(r"JSON\.stringify|serde_json|json\.dumps|structured|logfmt", re.IGNORECASE)
LEVEL_WORD = re.compile(r"\b(?:ERROR|WARN|WARNING|INFO|DEBUG|TRACE|FATAL)\b")
TIMESTAMP = re.compile(r"toISOString|Date\.now|time\.Now|datetime\.now|Utc::now|chrono::", re.IGNORECASE)
LOG_HELPER_DEF = re.compile(
    r"(?:export\s+)?(?:async\s+)?(?:function|const|fn|def)\s+(log[A-Za-z_]*|emit[A-Za-z_]*(?:Telemetry|Log|Event)|track[A-Za-z_]*)\b"
)
CORRELATION = re.compile(
    r"\b(?:correlation[_-]?id|request[_-]?id|requestId|traceId|trace[_-]?id|x-request-id|cf-ray|span[_-]?id)\b",
    re.IGNORECASE,
)
# A secret *value* reaching a log call — an identifier interpolated or passed
# as an argument — not the word appearing inside a message string.
# `logError('stripe_webhook_secret_not_configured', ...)` names a secret; it
# does not print one.
_SECRET_WORD = (r"(?:password|passwd|senha|password_hash|token|secret|api[_-]?key"
                r"|authorization|cookie|qr_secret|client_secret|private_key)")
PII_IN_LOG = re.compile(
    r"(?:console\.(?:log|error|warn|info)|println!|logError|emitTelemetry)\s*\("
    r"[^)]*?(?:"
    r"\$\{[^}]*\b" + _SECRET_WORD + r"\b[^}]*\}"        # `${user.token}` interpolated
    r"|(?<![\'\"\w.-])\b" + _SECRET_WORD + r"\b\s*[,)]"  # bare identifier passed as argument
    r"|\.\s*" + _SECRET_WORD + r"\b\s*[,)+]"             # `obj.password,` / `obj.token)`
    r"|[{,]\s*" + _SECRET_WORD + r"\b\s*[,}]"            # `{ token }` shorthand property
    r"|\b" + _SECRET_WORD + r"\s*:\s*(?!['\"])"          # `token: value` (not a literal string)
    r")",
    re.IGNORECASE | re.DOTALL,
)
REDACTION = re.compile(r"\bredact\w*|\bmask\w*|\bsanitiz\w*|\bscrub\w*|\[REDACTED\]|\*{3,}", re.IGNORECASE)
RETENTION = re.compile(
    r"\bretention\b|\bretenção\b|\bretencao\b|\bdias de retenção\b|\bdata retention\b|"
    r"\bkeep\s+logs?\s+for\b|\bdelete[sd]?\s+after\b|\bTTL\b|\bexpire[sd]?\s+after\b",
    re.IGNORECASE,
)
CONSENT = re.compile(r"\bconsent\w*|\bopt[-_ ]?in\b|\bconsentimento\b|\bRGPD\b|\bGDPR\b", re.IGNORECASE)
VERSION_IN_REPORT = re.compile(
    r"(?:version|commit|sha|build)\s*[:=]|process\.env\.npm_package_version|"
    r"CARGO_PKG_VERSION|__VERSION__|APP_VERSION|ASSET_VERSION",
    re.IGNORECASE,
)


def iter_files(root: Path, sub: str | None = None):
    base = root / sub if sub else root
    if not base.exists():
        return
    for p in base.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in CODE_EXT:
            continue
        if any(part in IGNORED for part in p.relative_to(root).parts):
            continue
        yield p


def rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def finding(check, result, reason, evidence=None, severity=""):
    return {"check": check, "result": result, "severity": severity,
            "reason": reason, "evidence": evidence or []}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--platform", default="web")
    ap.add_argument("--src", default=None, help="source subdirectory (default: autodetect src/ then repo root)")
    ap.add_argument("--docs", default="docs")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    repo = Path(a.repo).resolve()
    sub = a.src if a.src else ("src" if (repo / "src").is_dir() else None)
    files = list(iter_files(repo, sub))

    helpers: list[tuple[str, str]] = []        # (file:line, name)
    bare: list[str] = []
    structured_hits: list[str] = []
    corr_hits: list[str] = []
    pii_hits: list[str] = []
    redaction_hits: list[str] = []
    version_hits: list[str] = []

    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        r = rel(f, repo)
        for m in LOG_HELPER_DEF.finditer(text):
            line = text[:m.start()].count("\n") + 1
            helpers.append((f"{r}:{line}", m.group(1)))
        for m in BARE_LOG.finditer(text):
            line = text[:m.start()].count("\n") + 1
            window = text[max(0, m.start() - 200):m.start() + 300]
            if JSON_IN_LOG.search(window) or LEVEL_WORD.search(window):
                structured_hits.append(f"{r}:{line}")
            else:
                bare.append(f"{r}:{line}")
        for m in CORRELATION.finditer(text):
            line = text[:m.start()].count("\n") + 1
            corr_hits.append(f"{r}:{line}: {m.group(0)}")
        for m in PII_IN_LOG.finditer(text):
            line = text[:m.start()].count("\n") + 1
            pii_hits.append(f"{r}:{line}: {text.splitlines()[line-1].strip()[:110]}")
        if REDACTION.search(text):
            redaction_hits.append(r)
        for m in VERSION_IN_REPORT.finditer(text):
            line = text[:m.start()].count("\n") + 1
            version_hits.append(f"{r}:{line}")

    results: list[dict] = []

    # --- logs-structured
    if not files:
        results.append(finding("observability.logs-structured", "NOT_VERIFIED",
                               "missing-instrument: no source files found to inspect"))
    elif not helpers and not structured_hits:
        results.append(finding("observability.logs-structured", "FAIL",
                               f"no logging helper and no structured log call found in {len(files)} source files; "
                               f"{len(bare)} bare console/print call(s) — an incident leaves unparseable text",
                               bare[:5], severity="HIGH"))
    else:
        ev = [f"helper: {loc} -> {name}" for loc, name in helpers[:4]]
        ev.append(f"structured log calls: {len(structured_hits)}; bare calls: {len(bare)}")
        if bare:
            ev += [f"bare: {b}" for b in bare[:4]]
        ratio = len(structured_hits) / max(1, len(structured_hits) + len(bare))
        if ratio < 0.5:
            results.append(finding("observability.logs-structured", "FAIL",
                                   f"only {ratio:.0%} of log calls are structured; the rest are bare text "
                                   f"(static analysis of {len(files)} files)", ev, severity="MEDIUM"))
        else:
            results.append(finding("observability.logs-structured", "PASS",
                                   f"{ratio:.0%} of log calls are structured (JSON/level) via {len(set(n for _, n in helpers))} "
                                   f"helper(s); static analysis of {len(files)} files", ev))

    # --- correlation-id
    if corr_hits:
        results.append(finding("observability.correlation-id-e2e", "PASS",
                               f"a correlation identifier appears in {len(corr_hits)} place(s) (static analysis; "
                               f"crossing the boundary end-to-end is not proven here)", corr_hits[:5]))
    else:
        results.append(finding("observability.correlation-id-e2e", "FAIL",
                               "no correlation/request id anywhere in the source: two log lines from the same user "
                               "action cannot be tied together", severity="MEDIUM"))

    # --- pii-redacted
    if pii_hits:
        results.append(finding("observability.pii-redacted", "FAIL",
                               f"{len(pii_hits)} log call(s) interpolate a secret/PII-looking identifier",
                               pii_hits[:6], severity="HIGH"))
    else:
        ev = [f"redaction helpers in: {', '.join(sorted(set(redaction_hits))[:4])}"] if redaction_hits else []
        ev.append(f"scanned {len(files)} files for password/token/secret inside log calls: 0 hits")
        results.append(finding("observability.pii-redacted", "PASS",
                               "no secret or credential is interpolated into a log call (static analysis; "
                               "a captured production sample would be stronger)", ev))

    # --- retention-declared
    docs_hits: list[str] = []
    for d in [repo / a.docs, repo]:
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.md"))[:400]:
            if any(part in IGNORED for part in p.relative_to(repo).parts):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            m = RETENTION.search(text)
            if m:
                line = text[:m.start()].count("\n") + 1
                docs_hits.append(f"{rel(p, repo)}:{line}: {text.splitlines()[line-1].strip()[:100]}")
        if docs_hits:
            break
    if docs_hits:
        results.append(finding("observability.retention-declared", "PASS",
                               "a log/data retention policy is written down", docs_hits[:4]))
    else:
        results.append(finding("observability.retention-declared", "FAIL",
                               "no retention policy found in the documentation: nobody knows how long logs or "
                               "personal data are kept", severity="MEDIUM"))

    # --- telemetry-consent
    consent_code = [rel(f, repo) for f in files
                    if CONSENT.search(f.read_text(encoding="utf-8", errors="replace"))]
    telemetry_files = [rel(f, repo) for f in files if "telemetry" in f.name.lower()]
    if consent_code:
        results.append(finding("observability.telemetry-consent", "PASS",
                               f"consent handling exists in {len(consent_code)} file(s); telemetry modules: "
                               f"{', '.join(telemetry_files) or 'none'}",
                               consent_code[:5]))
    elif telemetry_files:
        results.append(finding("observability.telemetry-consent", "FAIL",
                               "telemetry is emitted but no consent/opt-in handling was found",
                               telemetry_files[:4], severity="HIGH"))
    else:
        results.append(finding("observability.telemetry-consent", "NOT_APPLICABLE",
                               "no telemetry module in the source"))

    # --- version-in-report
    if version_hits:
        results.append(finding("observability.version-in-report", "PASS",
                               f"version/commit identifiers are referenced in {len(version_hits)} place(s)",
                               version_hits[:5]))
    else:
        results.append(finding("observability.version-in-report", "FAIL",
                               "no version or commit identifier reaches any report: a customer bug cannot be "
                               "tied to a build", severity="MEDIUM"))

    # --- error-diagnosable: needs a real sample
    results.append(finding("observability.error-diagnosable", "NOT_VERIFIED",
                           "missing-instrument: needs a captured log sample from a real (or injected) incident, "
                           "read end-to-end; this instrument only reads source code"))

    # --- crash-report-opt-in: desktop
    if a.platform == "desktop" or a.platform == "both":
        results.append(finding("observability.crash-report-opt-in", "NOT_VERIFIED",
                               "missing-instrument: needs the desktop crash reporter configuration and a proof "
                               "that it is off by default"))

    print(json.dumps({"repo": str(repo), "platform": a.platform,
                      "files_scanned": len(files), "results": results},
                     indent=2, ensure_ascii=False))
    for r in results:
        print(f"  {r['result']:15} {r['check']:36} {r['reason'][:86]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
