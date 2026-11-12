#!/usr/bin/env python3
"""webhook_idempotency.py — code-audit, the inbound-contract idempotency predicate.

A webhook is an inbound contract the sender **retries**: Stripe, GitHub,
Svix and friends re-deliver an event until they get a 200, and they may
deliver the *same* event twice, concurrently. If the handler acts before it
claims the event — or claims it in a way that does not stop the second
delivery — a retry repeats the side effect: a second licence, a second
email, a second invoice.

This instrument answers one structural question, by reading the source:

    in the webhook handler, is the event **claimed** (a write keyed by the
    event id) **before** the irreversible side effects run, and does the
    claim **gate** them?

A claim gates when a duplicate cannot get past it: a plain insert/create on
the event key (the unique key throws), or an insert-if-absent (`ON CONFLICT
DO NOTHING`, `OR IGNORE`, `skipDuplicates`, `NX`) whose result is checked.
A read-then-insert-if-absent whose result is not checked is the race this
exists to catch: two deliveries both pass the read.

It is a **static** instrument and says so in every reason string. Where it
cannot recognise the claim it answers `NOT_VERIFIED`, never `FAIL`: a FAIL
is reserved for what the source shows — a claim after the side effect, a
guard never written back, or a handler with nothing that could deduplicate.
The behavioural proof is the project's `billing-harness` (`CONTRACTS §4.6`).

Comments are stripped before matching (offsets preserved). Test files are
not handlers, nor is a client that sends to the route.

Checks decided here:

  contract.webhook-idempotency-ordered   the claim precedes and gates every
                                         irreversible side effect

Output: JSON on stdout, human summary on stderr, exit 0.

Usage:
  python webhook_idempotency.py --repo . [--platform web|desktop|both] [--src src]
"""

from __future__ import annotations

import argparse
import functools
import json
import re
import sys
from pathlib import Path

CODE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
IGNORED = {".git", "node_modules", "dist", "build", "target", ".venv", "venv",
           "__pycache__", ".wrangler", "coverage", ".audit", ".verify", ".agents", "spikes",
           "test", "tests", "__tests__", "__mocks__", "e2e", "fixtures", ".next", ".svelte-kit"}
TEST_FILE = re.compile(r"\.(?:test|spec|e2e)\.[cm]?[jt]sx?$", re.IGNORECASE)

# A file is a webhook handler if it *receives* a webhook route, declares a webhook
# function, or lives on a webhook path (`app/api/stripe/webhook/route.ts`, a
# `webhook.ts`) **and** reads a request body. A route named in a comment, or a
# client that POSTs to it, is not a handler.
WEBHOOK_ROUTE = re.compile(r"[\"'`]/[\w./:-]*webhook", re.IGNORECASE)
CLIENT_CALL = re.compile(r"(?:\bfetch|\baxios(?:\.\w+)?|\bgot(?:\.\w+)?|\bky(?:\.\w+)?|"
                         r"\bsupertest\([^)]*\)\.\w+|\brequest\([^)]*\)\.\w+)\s*\(\s*$")
WEBHOOK_FN = re.compile(
    r"(?:async\s+)?function\s+\w*webhook\w*\s*\(|"
    r"(?:const|let|var)\s+\w*webhook\w*\s*=\s*(?:async\s*)?(?:\(|function\b)|"
    r"\bhandleWebhook\w*\s*\(|\bonWebhook\w*\s*\(",
    re.IGNORECASE,
)
# The receiving function of a framework route file (Next.js, SvelteKit, Remix, …).
ROUTE_EXPORT = re.compile(
    r"export\s+(?:async\s+)?function\s+(?:POST|handler|action)\s*\(|"
    r"export\s+const\s+(?:POST|handler|action)\s*(?::[^=]+)?=\s*(?:async\s*)?\(|"
    r"export\s+default\s+(?:async\s+)?function\s*\w*\s*\(",
)
REQUEST_BODY = re.compile(
    r"\breq(?:uest)?\.(?:text|json|arrayBuffer|formData|blob|body|rawBody)\b|"
    r"\.arrayBuffer\s*\(|constructEvent|verifySignature|verifyWebhook|\bWebhook\s*\(",
    re.IGNORECASE,
)

# Words that name the dedup store or a dedup helper — `processed_events`, `stripeEvent`,
# `markProcessed`, `alreadySeen`, `eventos`, `jaProcessado`.
EVENT_WORD = re.compile(r"event|evento|evt|webhook|processed|processad|idempot|dedup|"
                        r"seen|visto|claim|delivery|deliveries", re.IGNORECASE)
# A reference to an id — the claim and the guard are keyed by one.
ID_REF = re.compile(r"\.id\b|\bid\b|_id\b|[a-z]Id\b|\bevt_\w+")
# Vocabulary only a dedup uses — `event` alone is every Stripe handler's variable name.
DEDUP_WORD = re.compile(r"processed|processad|idempot|dedup|already|\bseen\b|visto|claim", re.IGNORECASE)

# SQL in a string: the guard read, and a write.
SQL_SELECT = re.compile(r"SELECT\s+[\w*.,\s]+?\s+FROM\s+(\w+)\s+WHERE\s+(\w+)\s*=", re.IGNORECASE)
SQL_INSERT = re.compile(r"INSERT\s+(?:OR\s+(\w+)\s+)?INTO\s+(\w+)", re.IGNORECASE)
# ORM / query builder / key-value.
ORM_READ = re.compile(r"\b(\w+)\.(?:findUnique|findFirst|findOne|findById|exists|count)\w*\s*\(", re.IGNORECASE)
ORM_CREATE = re.compile(r"\b(\w+)\.(create|createMany|insert|insertOne|upsert)\s*\(", re.IGNORECASE)
DRIZZLE_INSERT = re.compile(r"\.insert\s*\(\s*(\w+)\s*\)")
# Supabase: a duplicate insert returns `{ error }` instead of throwing, so it gates only if read.
SUPA_SELECT = re.compile(r"\.from\(\s*[\"'`](\w+)[\"'`]\s*\)\s*\.select\s*\(")
SUPA_INSERT = re.compile(r"\.from\(\s*[\"'`](\w+)[\"'`]\s*\)\s*\.(insert|upsert)\s*\(")
KV_READ = re.compile(r"\b(\w+)\.(?:get|has|exists)\s*\(", re.IGNORECASE)
KV_WRITE = re.compile(r"\b(\w+)\.(put|set|setnx|setNX|add)\s*\(", re.IGNORECASE)
# A helper whose name says it is the dedup: `alreadyProcessed(id)`, `claimEvent(id)`.
HELPER = re.compile(r"\b((?:already|is|was|has|ja|mark|claim|record|save|registar|marcar)\w*)\s*\(",
                    re.IGNORECASE)

# Insert-if-absent: re-running it is harmless, so it gates only if its result is read.
IF_ABSENT = re.compile(r"ON\s+CONFLICT|OR\s+(?:IGNORE|REPLACE)|skipDuplicates|onConflictDoNothing|"
                       r"\bupsert\b|[\"']NX[\"']|\bNX\s*:|setnx|\.put\s*\(", re.IGNORECASE)
RESULT_READ = re.compile(r"\b(?:changes|rowCount|affectedRows|numInsertedOrUpdatedRows|count)\b|RETURNING",
                         re.IGNORECASE)

# Irreversible side effects: a call that leaves the process. `fetch(` as a call, not
# the Worker's `async fetch(req, env)` entry method; read-only SDK calls are not effects.
SIDE_CALL = re.compile(
    r"(?<!async )(?<!function )\bfetch\s*\(|"
    r"\bstripe\.(?!webhooks\b)\w+\.(?:create|update|del|cancel|pay|finalize|send|void|capture|refund)\w*\s*\(|"
    r"\.(?:emails|messages|mail)\.(?:send|create)\s*\(|\bsendMail\s*\(|"
    r"\bawait\s+\w*(?:send|email|mail|notify|publish|grant|issue|provision|activate|fulfil|deliver|"
    r"charge|refund|invoice|mandar|enviar|emitir|factur|cobrar|ativar|conceder)\w*\s*\(",
    re.IGNORECASE,
)


def strip_comments(text: str) -> str:
    """Blank out `//` and `/* */` comments, keeping the length and the newlines so
    offsets (and line numbers) do not move. Strings are skipped, so `http://` inside
    a literal is not read as a comment."""
    out = list(text)
    i, n, state = 0, len(text), None
    while i < n:
        c = text[i]
        if state is None:
            if c == "/" and i + 1 < n and text[i + 1] == "/":
                state = "line"; out[i] = out[i + 1] = " "; i += 2; continue
            if c == "/" and i + 1 < n and text[i + 1] == "*":
                state = "block"; out[i] = out[i + 1] = " "; i += 2; continue
            if c in "\"'`":
                q = c; i += 1
                while i < n and text[i] != q:
                    i += 2 if text[i] == "\\" else 1
                i += 1
                continue
            i += 1
        elif state == "line":
            if c == "\n":
                state = None
            else:
                out[i] = " "
            i += 1
        else:  # block
            if c == "*" and i + 1 < n and text[i + 1] == "/":
                out[i] = out[i + 1] = " "; state = None; i += 2; continue
            if c != "\n":
                out[i] = " "
            i += 1
    return "".join(out)


@functools.lru_cache(maxsize=8)
def mask_strings(code: str) -> str:
    """`code` with the inside of every string literal blanked, the quotes and the length
    kept: what the structure is read from, so a `;`, a newline or a bracket inside a
    (multi-line) SQL literal does not end a statement. `'` and `"` stop at a newline —
    an unterminated one cannot swallow the file; a template literal spans lines and its
    `${…}` is blanked with it."""
    out = list(code)
    i, n = 0, len(code)
    while i < n:
        q = code[i]
        if q not in "\"'`":
            i += 1
            continue
        i += 1
        while i < n and code[i] != q and (q == "`" or code[i] != "\n"):
            step = 2 if code[i] == "\\" else 1
            for k in range(i, min(n, i + step)):
                out[k] = " "
            i += step
        i += 1
    return "".join(out)


def iter_files(root: Path, sub: str | None):
    base = root / sub if sub else root
    if not base.exists():
        return
    for p in base.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in CODE_EXT or TEST_FILE.search(p.name):
            continue
        if any(part in IGNORED for part in p.relative_to(root).parts):
            continue
        yield p


def rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def line_of(text: str, off: int) -> int:
    return text[:off].count("\n") + 1


def finding(result, reason, evidence=None, severity=""):
    return {"check": "contract.webhook-idempotency-ordered", "result": result,
            "severity": severity, "reason": reason, "evidence": evidence or []}


def receives_route(code: str) -> bool:
    """A webhook route string that is not the target of an outgoing client call."""
    for m in WEBHOOK_ROUTE.finditer(code):
        if not CLIENT_CALL.search(code[max(0, m.start() - 60):m.start()]):
            return True
    return False


def is_handler(path: Path, root: Path, code: str) -> bool:
    if receives_route(code) or WEBHOOK_FN.search(code):
        return True
    on_webhook_path = any("webhook" in part.lower() for part in path.relative_to(root).parts)
    return on_webhook_path and bool(REQUEST_BODY.search(code))


def handler_body(code: str) -> tuple[str, int]:
    """The webhook function's body (brace-matched) and its offset; whole file if not found.

    Scoping matters: a `fetch` or a mail helper elsewhere in the file is not a side
    effect of *this* handler, and counting it would point the finding at the wrong line.
    """
    m = WEBHOOK_FN.search(code) or ROUTE_EXPORT.search(code)
    if not m:
        return code, 0
    s = mask_strings(code)  # a `{` inside a literal opens nothing
    i = s.find("{", m.end())
    if i < 0:
        return code, 0
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return code[i:j + 1], i
    return code, 0


CONTINUES = tuple("=(,.+-?:&|[{")


def statement(body: str, off: int) -> tuple[str, int, int]:
    """The statement around `off`: back to the `;`, the enclosing block's `{`, or the
    newline that ended the previous statement (no-semicolon style) — skipping balanced
    brackets, so `const { rowCount } = await …(` stays one statement — and forward to
    the `;` or newline where the brackets opened since `off` close. The structure is
    read with string contents blanked; the text returned is the original."""
    s = mask_strings(body)
    depth, start = 0, 0
    for j in range(off - 1, -1, -1):
        c = s[j]
        if c in ")]}":
            depth += 1
        elif c in "([":
            depth = max(0, depth - 1)  # an unmatched one: `off` is inside a call's arguments
        elif c == "{":
            if depth == 0:
                start = j + 1
                break
            depth -= 1
        elif depth == 0 and c == ";":
            start = j + 1
            break
        elif depth == 0 and c == "\n":
            before = s[max(0, j - 200):j].rstrip()
            after = s[j + 1:off].lstrip()
            if before and not before.endswith(CONTINUES) and not after.startswith((".", "?", ":")):
                start = j + 1
                break
    depth, end, cap = 0, None, min(len(body), off + 800)
    for j in range(off, cap):
        c = s[j]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
            if depth < 0:
                end = j
                break
        elif depth == 0 and c == ";":
            end = j
            break
        elif depth == 0 and c == "\n":
            if not s[off:j].rstrip().endswith(CONTINUES) and \
                    not s[j + 1:cap].lstrip().startswith("."):
                end = j
                break
    end = cap if end is None else end
    return body[start:end], start, end


def gates_on_result(body: str, stmt: str, end: int) -> bool:
    """The claim's result is read: the statement is a condition, reads a row count
    inline, or assigns a name that a following `if` reads."""
    head = stmt.lstrip()
    if head.startswith(("if", "return", "!")) or RESULT_READ.search(stmt):
        return True
    m = re.match(r"(?:const|let|var)\s+(\w+|\{[^}]*\}|\[[^\]]*\])\s*=", head)
    if not m:
        return False
    names = re.findall(r"\w+", m.group(1))
    after = body[end:end + 400]
    return any(re.search(r"\bif\s*\([^)]*\b" + re.escape(n) + r"\b", after) for n in names)


def collect(body: str) -> tuple[list, list, list]:
    """(claims, guards, side_effects). A claim is (offset, gates, label); a guard is
    (offset, store, label); a side effect is an offset."""
    claims: list[tuple[int, bool, str]] = []
    guards: list[tuple[int, str, str]] = []
    side: list[int] = [m.start() for m in SIDE_CALL.finditer(body)]

    for m in SQL_SELECT.finditer(body):
        # Keyed by the event: an event store, or an event-id column (not `users.id`).
        if EVENT_WORD.search(m.group(1)) or re.search(r"event|evt", m.group(2), re.IGNORECASE):
            guards.append((m.start(), m.group(1).lower(), f"SELECT FROM {m.group(1)} WHERE {m.group(2)}"))
    for m in ORM_READ.finditer(body):
        stmt, _, _ = statement(body, m.start())
        if EVENT_WORD.search(m.group(1)) and ID_REF.search(stmt):
            guards.append((m.start(), m.group(1).lower(), f"{m.group(1)}.{m.group(0).split('.')[-1].strip('( ')}"))
    for m in SUPA_SELECT.finditer(body):
        if EVENT_WORD.search(m.group(1)):
            guards.append((m.start(), m.group(1).lower(), f"from('{m.group(1)}').select"))
    for m in KV_READ.finditer(body):
        stmt, _, _ = statement(body, m.start())
        if EVENT_WORD.search(stmt) and ID_REF.search(stmt):
            guards.append((m.start(), m.group(1).lower(), f"{m.group(1)}.get"))

    guard_stores = {g[1] for g in guards}

    def write(off: int, store: str, label: str, if_absent: bool = False) -> None:
        stmt, _, end = statement(body, off)
        is_claim = (store.lower() in guard_stores or EVENT_WORD.search(store)) and ID_REF.search(stmt)
        if not is_claim:
            if not IF_ABSENT.search(stmt):
                side.append(off)  # a write that can duplicate: a side effect of its own
            return
        if_absent = if_absent or bool(IF_ABSENT.search(stmt))
        claims.append((off, (not if_absent) or gates_on_result(body, stmt, end), label))

    for m in SQL_INSERT.finditer(body):
        write(m.start(), m.group(2), f"INSERT INTO {m.group(2)}")
    for m in ORM_CREATE.finditer(body):
        if m.group(1).lower() in {"db", "tx", "knex", "trx"} and m.group(2).lower() == "insert":
            continue  # query-builder insert: the table is the argument (below)
        write(m.start(), m.group(1), f"{m.group(1)}.{m.group(2)}")
    for m in DRIZZLE_INSERT.finditer(body):
        write(m.start(), m.group(1), f"insert({m.group(1)})")
    for m in SUPA_INSERT.finditer(body):
        write(m.start(), m.group(1), f"from('{m.group(1)}').{m.group(2)}", if_absent=True)
    for m in KV_WRITE.finditer(body):
        stmt, _, _ = statement(body, m.start())
        if EVENT_WORD.search(stmt) and ID_REF.search(stmt):
            write(m.start(), "event", f"{m.group(1)}.{m.group(2)}")

    for m in HELPER.finditer(body):
        name = m.group(1)
        if not EVENT_WORD.search(name):
            continue
        stmt, _, end = statement(body, m.start())
        if not ID_REF.search(stmt):
            continue
        if re.match(r"(?:already|is|was|has|ja)", name, re.IGNORECASE):
            guards.append((m.start(), "helper", f"{name}()"))
        else:  # mark/claim/record: the helper's insides are not visible from here
            claims.append((m.start(), gates_on_result(body, stmt, end), f"{name}()"))
    return claims, guards, side


def judge(body: str, base: int, full: str, where: str) -> dict:
    """The verdict for one handler file (already known to be a handler)."""
    line = lambda off: line_of(full, base + off)  # noqa: E731
    claims, guards, side = collect(body)
    claim_offs = {c[0] for c in claims}
    side = sorted(s for s in set(side) if s not in claim_offs)

    if not side:
        return finding("NOT_VERIFIED",
                       f"static analysis: `{where}` looks like a webhook handler but no irreversible "
                       f"side effect was seen to order a claim against")
    earliest = side[0]

    if not claims:
        if guards and all(g[1] != "helper" for g in guards):
            off, store, label = guards[0]
            return finding("FAIL",
                           f"static analysis: `{where}` guards on `{label}` but never writes the claim "
                           f"back; a retry that arrives before the write repeats the side effects",
                           [f"handler: {where}", f"guard read: {label} (line {line(off)})",
                            f"first side effect (line {line(earliest)})"],
                           severity="HIGH")
        if guards or DEDUP_WORD.search(body):
            return finding("NOT_VERIFIED",
                           f"static analysis: `{where}` has side effects and something that may "
                           f"deduplicate, but no claim keyed by the event id was recognised; prove "
                           f"it with the billing-harness (a duplicate delivery repeats nothing)",
                           [f"handler: {where}", f"first side effect (line {line(earliest)})"])
        return finding("FAIL",
                       f"static analysis: `{where}` has side effects and nothing that deduplicates the "
                       f"event (no read or write keyed by the event id); a retried delivery repeats them",
                       [f"handler: {where}", f"first side effect (line {line(earliest)})"],
                       severity="HIGH")

    off, gates, label = min(claims)
    ev = [f"handler: {where}", f"claim: {label} (line {line(off)})",
          f"first side effect (line {line(earliest)})"]
    if guards:
        ev.insert(1, f"guard read: {guards[0][2]} (line {line(guards[0][0])})")

    if off > earliest:
        return finding("FAIL",
                       f"static analysis: in `{where}` the claim ({label}, line {line(off)}) runs AFTER "
                       f"the first side effect (line {line(earliest)}); a concurrent or retried "
                       f"delivery repeats it",
                       ev, severity="BLOCKER")
    if not gates:
        return finding("NOT_VERIFIED",
                       f"static analysis: in `{where}` the claim ({label}, line {line(off)}) precedes "
                       f"the side effects but does not gate them: it is insert-if-absent and its result "
                       f"is not read, so two concurrent deliveries both pass; read the affected-row "
                       f"count (or insert without the if-absent) and prove it with the billing-harness",
                       ev)
    return finding("PASS",
                   f"static analysis: in `{where}` the event is claimed ({label}) before every side "
                   f"effect and a duplicate cannot get past the claim; prove the behaviour with the "
                   f"billing-harness", ev)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--platform", default="web")
    ap.add_argument("--src", default=None, help="narrow to a subdirectory (default: the whole repo)")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    repo = Path(a.repo).resolve()

    if a.platform == "desktop":
        results = [finding("NOT_APPLICABLE",
                           "static analysis: a desktop build has no inbound webhook to deduplicate")]
    else:
        files = list(iter_files(repo, a.src))
        verdicts: list[tuple[int, dict]] = []
        for f in files:
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            code = strip_comments(text)
            if not is_handler(f, repo, code):
                continue
            body, base = handler_body(code)
            v = judge(body, base, text, rel(f, repo))
            rank = {"FAIL": 0, "NOT_VERIFIED": 1, "PASS": 2, "NOT_APPLICABLE": 3}[v["result"]]
            verdicts.append((rank, v))

        if not verdicts:
            results = [finding("NOT_APPLICABLE",
                               f"static analysis: no webhook handler found in {len(files)} source files")]
        else:
            results = [min(verdicts, key=lambda x: x[0])[1]]

    print(json.dumps({"repo": str(repo), "platform": a.platform, "results": results},
                     indent=2, ensure_ascii=False))
    for r in results:
        print(f"  {r['result']:15} {r['check']:40} {r['reason'][:80]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
