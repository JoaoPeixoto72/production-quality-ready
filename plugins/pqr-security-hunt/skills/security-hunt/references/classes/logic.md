# Classes — business logic

Owner: `security-hunt`. Card format and fields: see the head of
`isolation.md`. Scanners do not find these; read each workflow end to end.

### logic.state-skip
- **Check:** `sec.business-logic-abuse`
- **Invariant:** a workflow moves only along its declared transitions, enforced on the server.
- **Where it hides:** a status field written by a generic update; a transition checked in the UI; "accept" reachable from "draft"; re-opening a closed record to edit what closing froze.
- **Red test:** request a transition the state machine forbids; assert refusal and unchanged state.
- **Not a finding:** a transition the domain rules list as allowed.

### logic.replay
- **Check:** `sec.business-logic-abuse`
- **Invariant:** an action with an external effect (create a project from a quote, issue an invoice, send money, send an email to a client) happens once per intent.
- **Where it hides:** accept or convert endpoints without an idempotency key or a unique constraint; retries after a lost response; a double click that reaches two handlers.
- **Red test:** send the same action twice (sequentially and concurrently in a local fixture); assert one effect.
- **Not a finding:** a unique constraint or claim row that makes the second call a no-op, cited.

### logic.check-then-act
- **Check:** `sec.business-logic-abuse`
- **Invariant:** a limit (seats, quota, stock, balance, one-active-item) is enforced atomically with the write it limits.
- **Where it hides:** `SELECT count` then `INSERT` in separate statements; a quota read, compared in code, then written.
- **Red test:** fire N concurrent requests just under the limit in a local fixture; assert the limit holds.
- **Not a finding:** a single conditional statement or a batch the database runs atomically.

### logic.numeric
- **Check:** `sec.business-logic-abuse`
- **Invariant:** quantities and money are bounded, signed as the domain requires, and computed in integers.
- **Where it hides:** negative amounts or quantities accepted; percentages above 100%; floating-point money; overflow past the integer range; rounding that favours the caller on repetition.
- **Red test:** send the boundary value (negative, zero, huge, fractional); assert refusal or the exact integer result.
- **Not a finding:** a value the schema bounds, cited.

### logic.fail-open
- **Check:** `sec.business-logic-abuse`
- **Invariant:** a missing secret, absent config, disabled feature flag or failed dependency leaves the control closed.
- **Where it hides:** `if (!secret) return next()`; signature verification skipped when the header is absent; a toggle that disables a check instead of a feature; `catch` that continues as authorised.
- **Red test:** run the path with the config absent or the dependency failing; assert the request is refused.
- **Not a finding:** a fail-open the threat model accepts by name (an optional anti-bot widget), cited.

### logic.time-window
- **Check:** `sec.business-logic-abuse`
- **Invariant:** expiry and scheduling compare times in one clock and one unit, inclusive or exclusive as the rule says.
- **Where it hides:** seconds compared with milliseconds; local time against UTC; `<=` vs `<` at expiry; client-sent timestamps trusted.
- **Red test:** use a token or offer exactly at, and one unit after, its expiry; assert the rule.
- **Not a finding:** a boundary off by one unit the domain does not care about.

### logic.declared-size
- **Check:** `sec.business-logic-abuse`
- **Invariant:** a quota, credit or balance moves by what the server measured, never by a size, count or amount the caller declares or a snapshot carries.
- **Where it hides:** a restore or import that charges the `size_bytes` written in the snapshot; an upload metered by `Content-Length` or a body field rather than bytes stored; a delete that refunds the stored declared value, so a small declared charge and a large refund drive the quota negative or to zero.
- **Red test:** import or upload with a declared size far from the real one (zero, huge, negative), then delete; assert the quota equals the measured bytes before, during and after.
- **Not a finding:** a declared value the server overwrites with its own measurement before it is stored, cited.
