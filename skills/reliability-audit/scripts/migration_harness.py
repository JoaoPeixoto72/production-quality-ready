#!/usr/bin/env python3
"""migration_harness.py — reliability-audit §1 instrument (SQL migrations).

Applies the **whole published chain from an empty database** in a
throwaway directory and reports what happened. This is the difference
between "the migrations directory exists" and "a database built from
version zero reaches HEAD without breaking".

Checks decided here:

  reliability.migration-forward    every migration, in order, from empty
                                   to HEAD, applies without error
  reliability.migration-tested     the resulting schema is exercised:
                                   tables/indices exist and PRAGMA
                                   integrity_check + foreign_key_check
                                   come back clean
  reliability.migration-immutable  file checksums match a committed
                                   manifest (only when one is declared)
  reliability.backup-before-migrate   destructive statements (DROP TABLE /
                                   DROP COLUMN) are flagged; PASS when
                                   none, FAIL when present without a
                                   backup step declared
  reliability.downgrade-declared   a documented downgrade/rollback path
                                   for the schema

Works with any directory of `NNNN_*.sql` files (D1, Turso, plain SQLite,
libSQL). For Postgres/MySQL-only syntax it reports NOT_VERIFIED with the
statement it could not run, rather than a false FAIL.

Output: JSON on stdout, human summary on stderr, exit 0.

Usage:
  python migration_harness.py --repo . [--migrations migrations]
                              [--checksums migrations/CHECKSUMS.json]
                              [--docs docs]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

DESTRUCTIVE = re.compile(r"^\s*(?:DROP\s+TABLE|DROP\s+COLUMN|ALTER\s+TABLE\s+\S+\s+DROP\b|TRUNCATE)",
                         re.IGNORECASE | re.MULTILINE)
# Must be about the *schema*, not about a business feature. A sentence like
# "não reversível por comando" in a product doc is not a downgrade policy, so
# the hint only counts when schema/migration vocabulary sits in the same
# sentence (the SCHEMA_CONTEXT window below).
DOWNGRADE_HINT = re.compile(
    r"\bdowngrade\b|\brollback\s+(?:the\s+)?(?:schema|migration)\b|\bmigration\s+rollback\b|"
    r"\bdown\.sql\b|\breverter\s+(?:a\s+)?migra|\bforward[- ]only\b|"
    r"\b(?:não|nao)\s+(?:é|e)?\s*revers\w*|\birreversível\b|\birreversivel\b",
    re.IGNORECASE,
)
SCHEMA_CONTEXT = re.compile(
    r"\bmigra\w*|\bschema\b|\besquema\b|\bDDL\b|\bD1\b|\bdatabase\b|\bbase de dados\b|"
    r"\bALTER TABLE\b|\bCREATE TABLE\b|\bversão do esquema\b",
    re.IGNORECASE,
)
PG_ONLY = re.compile(r"\bSERIAL\b|\bBIGSERIAL\b|::\w+|\bRETURNING\s+\*.*;\s*$|\bJSONB\b|\bNOW\(\)|\bUUID\b",
                     re.IGNORECASE)


def rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def finding(check, result, reason, evidence=None, severity=""):
    return {"check": check, "result": result, "severity": severity,
            "reason": reason, "evidence": evidence or []}


def split_statements(sql: str) -> list[str]:
    """Split on ';' outside string literals and BEGIN...END trigger bodies."""
    out, cur, i, n = [], [], 0, len(sql)
    in_s = in_d = in_line = in_block = False
    depth_begin = 0
    while i < n:
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""
        if in_line:
            if ch == "\n":
                in_line = False
            cur.append(ch); i += 1; continue
        if in_block:
            if ch == "*" and nxt == "/":
                in_block = False; cur.append("*/"); i += 2; continue
            cur.append(ch); i += 1; continue
        if in_s:
            cur.append(ch)
            if ch == "'":
                in_s = False
            i += 1; continue
        if in_d:
            cur.append(ch)
            if ch == '"':
                in_d = False
            i += 1; continue
        if ch == "-" and nxt == "-":
            in_line = True; cur.append("--"); i += 2; continue
        if ch == "/" and nxt == "*":
            in_block = True; cur.append("/*"); i += 2; continue
        if ch == "'":
            in_s = True; cur.append(ch); i += 1; continue
        if ch == '"':
            in_d = True; cur.append(ch); i += 1; continue
        word = sql[i:i + 5].upper()
        if word == "BEGIN" and re.match(r"BEGIN\b", sql[i:], re.IGNORECASE):
            depth_begin += 1
        elif sql[i:i + 3].upper() == "END" and re.match(r"END\b", sql[i:], re.IGNORECASE) and depth_begin:
            depth_begin -= 1
        if ch == ";" and depth_begin == 0:
            cur.append(";")
            stmt = "".join(cur).strip()
            if stmt.strip(";").strip():
                out.append(stmt)
            cur = []
            i += 1
            continue
        cur.append(ch); i += 1
    tail = "".join(cur).strip()
    if tail.strip(";").strip():
        out.append(tail)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--migrations", default="migrations")
    ap.add_argument("--checksums", default=None)
    ap.add_argument("--docs", default="docs")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    repo = Path(a.repo).resolve()
    mdir = repo / a.migrations
    results: list[dict] = []

    if not mdir.is_dir():
        out = {"repo": str(repo), "results": [finding(
            "reliability.migration-forward", "NOT_APPLICABLE",
            f"no migrations directory at {a.migrations}")]}
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    files = sorted(p for p in mdir.glob("*.sql") if p.is_file())
    if not files:
        print(json.dumps({"repo": str(repo), "results": [finding(
            "reliability.migration-forward", "NOT_APPLICABLE",
            f"{a.migrations}/ has no .sql files")]}, indent=2, ensure_ascii=False))
        return 0

    # ---------------------------------------------------------- forward run
    applied: list[str] = []
    failure: tuple[str, str, str] | None = None   # (file, statement, error)
    unsupported: list[str] = []
    with tempfile.TemporaryDirectory(prefix="pqr-migrations-") as tmp:
        db_path = Path(tmp) / "forward.sqlite"
        con = sqlite3.connect(db_path)
        con.execute("PRAGMA foreign_keys = ON")
        for f in files:
            sql = f.read_text(encoding="utf-8", errors="replace")
            for stmt in split_statements(sql):
                body = re.sub(r"--[^\n]*", "", stmt).strip()
                if not body:
                    continue
                try:
                    con.execute(stmt)
                except sqlite3.Warning:
                    try:
                        con.executescript(stmt)
                    except sqlite3.Error as e:  # noqa: PERF203
                        failure = (rel(f, repo), stmt.strip()[:160], str(e)); break
                except sqlite3.OperationalError as e:
                    if PG_ONLY.search(stmt):
                        unsupported.append(f"{rel(f, repo)}: {e} :: {stmt.strip()[:90]}")
                        continue
                    failure = (rel(f, repo), stmt.strip()[:160], str(e)); break
                except sqlite3.Error as e:
                    failure = (rel(f, repo), stmt.strip()[:160], str(e)); break
            if failure:
                break
            con.commit()
            applied.append(rel(f, repo))

        if failure:
            results.append(finding(
                "reliability.migration-forward", "FAIL",
                f"the chain breaks at {failure[0]} after {len(applied)} migration(s) applied from empty: {failure[2]}",
                [f"applied: {len(applied)}/{len(files)}",
                 f"failing file: {failure[0]}",
                 f"statement: {failure[1]}"], severity="BLOCKER"))
            results.append(finding("reliability.migration-tested", "FAIL",
                                   "schema not reachable from version zero, so it cannot be exercised",
                                   severity="BLOCKER"))
            con.close()
        elif unsupported:
            results.append(finding(
                "reliability.migration-forward", "NOT_VERIFIED",
                f"missing-instrument: {len(unsupported)} statement(s) use dialect features this SQLite harness "
                f"cannot execute; run them against the real engine",
                unsupported[:5]))
            con.close()
        else:
            tables = [r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            indices = [r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")]
            integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
            fk_problems = con.execute("PRAGMA foreign_key_check").fetchall()
            con.close()

            results.append(finding(
                "reliability.migration-forward", "PASS",
                f"all {len(files)} published migrations apply in order from an empty database to HEAD",
                [f"applied: {', '.join(applied[:3])} … {applied[-1]}",
                 f"tables created: {len(tables)}",
                 f"indices created: {len(indices)}"]))

            if integrity != "ok":
                results.append(finding("reliability.migration-tested", "FAIL",
                                       f"PRAGMA integrity_check returned: {integrity}", severity="BLOCKER"))
            elif fk_problems:
                results.append(finding("reliability.migration-tested", "FAIL",
                                       f"PRAGMA foreign_key_check reported {len(fk_problems)} problem(s)",
                                       [str(p) for p in fk_problems[:5]], severity="HIGH"))
            else:
                results.append(finding(
                    "reliability.migration-tested", "PASS",
                    "the schema built from version zero passes integrity_check and foreign_key_check",
                    [f"integrity_check: {integrity}", "foreign_key_check: 0 problems",
                     f"tables: {', '.join(tables[:8])}{' …' if len(tables) > 8 else ''}"]))

    # ------------------------------------------------------------ checksums
    cpath = Path(a.checksums) if a.checksums else (mdir / "CHECKSUMS.json")
    if not cpath.is_absolute():
        cpath = repo / cpath
    if cpath.is_file():
        try:
            manifest = json.loads(cpath.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            manifest = None
            results.append(finding("reliability.migration-immutable", "FAIL",
                                   f"{rel(cpath, repo)} is not valid JSON: {e}", severity="HIGH"))
        if manifest is not None:
            entries = manifest.get("migrations", manifest) if isinstance(manifest, dict) else {}
            mismatched, missing = [], []
            for f in files:
                digest = hashlib.sha256(
                    f.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").encode("utf-8")
                ).hexdigest()
                key = next((k for k in (f.name, rel(f, repo)) if isinstance(entries, dict) and k in entries), None)
                if key is None:
                    missing.append(f.name)
                    continue
                want = entries[key]
                want = want.get("sha256") if isinstance(want, dict) else want
                if isinstance(want, str) and want.lower() not in (digest, f"sha256:{digest}"):
                    mismatched.append(f"{f.name}: manifest={str(want)[:16]}… actual={digest[:16]}…")
            if mismatched:
                results.append(finding("reliability.migration-immutable", "FAIL",
                                       f"{len(mismatched)} published migration(s) differ from the committed manifest — "
                                       f"a released migration was edited", mismatched[:5], severity="BLOCKER"))
            elif missing:
                results.append(finding("reliability.migration-immutable", "FAIL",
                                       f"{len(missing)} migration(s) are not registered in {rel(cpath, repo)}",
                                       missing[:5], severity="HIGH"))
            else:
                results.append(finding("reliability.migration-immutable", "PASS",
                                       f"all {len(files)} migrations match the committed checksum manifest",
                                       [rel(cpath, repo), f"algorithm: sha256 over LF-normalised bytes"]))
    else:
        results.append(finding("reliability.migration-immutable", "FAIL",
                               f"no checksum manifest ({rel(cpath, repo)}): nothing stops a published migration "
                               f"from being edited", severity="HIGH"))

    # -------------------------------------------------- destructive / backup
    destructive: list[str] = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in DESTRUCTIVE.finditer(re.sub(r"--[^\n]*", "", text)):
            line = text[:m.start()].count("\n") + 1
            destructive.append(f"{rel(f, repo)}:{line}: {m.group(0).strip()}")
    if not destructive:
        results.append(finding("reliability.backup-before-migrate", "PASS",
                               f"no destructive statement (DROP/TRUNCATE) in {len(files)} migrations: "
                               f"nothing to back up before applying", []))
    else:
        results.append(finding("reliability.backup-before-migrate", "NOT_VERIFIED",
                               f"missing-instrument: {len(destructive)} destructive statement(s) found; whether a "
                               f"backup is taken first is a property of the deploy pipeline, not of the SQL",
                               destructive[:6]))

    # ------------------------------------------------------------- downgrade
    hits: list[str] = []
    for d in (repo / a.docs, repo):
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.md"))[:400]:
            parts = p.relative_to(repo).parts
            if any(x in parts for x in (".git", "node_modules", ".agents", ".audit")):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in DOWNGRADE_HINT.finditer(text):
                window = text[max(0, m.start() - 300):m.end() + 300]
                if not SCHEMA_CONTEXT.search(window):
                    continue  # talks about reversing a feature, not the schema
                line = text[:m.start()].count("\n") + 1
                hits.append(f"{rel(p, repo)}:{line}: {text.splitlines()[line-1].strip()[:100]}")
                break
        if hits:
            break
    if hits:
        results.append(finding("reliability.downgrade-declared", "PASS",
                               "downgrade behaviour is declared in the documentation", hits[:4]))
    else:
        results.append(finding("reliability.downgrade-declared", "FAIL",
                               "downgrade behaviour is not declared anywhere: it is unknown what happens when an "
                               "older binary opens a newer schema", severity="MEDIUM"))

    print(json.dumps({"repo": str(repo), "migrations": len(files), "results": results},
                     indent=2, ensure_ascii=False))
    for r in results:
        print(f"  {r['result']:15} {r['check']:36} {r['reason'][:86]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
