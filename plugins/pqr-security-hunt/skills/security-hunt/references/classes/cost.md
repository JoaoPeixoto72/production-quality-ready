# Classes — abuse of shared resources and operator money

Owner: `security-hunt`. Card format and fields: see the head of
`isolation.md`. On metered platforms (serverless CPU, database rows read,
paid email or SMS, invoice APIs) cost is a security boundary: a low-trust
caller spending the operator's quota takes the service down for everyone.
Prove with counted work in a local fixture, never against a live service.

### cost.preauth-work
- **Check:** `sec.anti-automation`
- **Invariant:** before authentication, a request costs a small bounded amount of work.
- **Where it hides:** hashing, PDF or image rendering, outbound email, or wide queries reachable by an anonymous route; a limiter that runs after the expensive step.
- **Red test:** call the anonymous route in a fixture with the expensive step instrumented; assert the limiter refuses before the step runs past the declared bound.
- **Not a finding:** work bounded by a limiter that runs first, cited.

### cost.query-amplification
- **Check:** `sec.anti-automation`
- **Invariant:** one request reads a number of rows bounded by a page size the server fixes.
- **Where it hides:** a list without `LIMIT` or with a caller-chosen limit; a subquery or extra query per row; a search with a leading wildcard over a large table; counts recomputed on every request.
- **Red test:** seed more rows than the page size, call with the largest limit the API accepts; assert the rows returned (or read, where the local engine reports it) stay at the bound.
- **Not a finding:** a table bounded by the domain (a tenant's settings).

### cost.unbounded-fanout
- **Check:** `sec.anti-automation`
- **Invariant:** one caller action triggers a bounded number of outbound effects (emails, notifications, webhooks, jobs).
- **Where it hides:** a recipient list from the request; a broadcast to every member on every edit; a retry loop without a cap.
- **Red test:** perform the action with the largest input accepted; assert the count of queued effects stays at the bound.
- **Not a finding:** fan-out bounded by a plan limit enforced on the server.

### cost.paid-provider
- **Check:** `sec.anti-automation`
- **Invariant:** a low-trust caller cannot make the operator pay a third party at will (email, SMS, invoicing, AI, maps).
- **Where it hides:** a resend button without a cooldown; a public form that sends email to an address it supplies; invoice creation reachable by a client role.
- **Red test:** repeat the action in a fixture with the provider stubbed; assert the stub is called at most the allowed number of times.
- **Not a finding:** a provider call behind a limiter and a role check, both cited.

### cost.limiter-gap
- **Check:** `sec.anti-automation`
- **Invariant:** the rate limiter counts every request of the class it protects.
- **Where it hides:** requests with no client IP skipped; per-instance counters on a platform that runs many instances; a reset on deploy; a key the caller can rotate.
- **Red test:** send requests in the shape the gap admits (no IP header, rotating key); assert the limit still trips.
- **Not a finding:** a skipped class proven to come only from a trusted internal caller.

### cost.client-loop
- **Check:** `sec.anti-automation`
- **Invariant:** shipped client code cannot turn one user into an unbounded request source.
- **Where it hides:** reconnect without backoff, or backoff reset on open; refresh loops driven by reactive state; polling that continues in hidden tabs.
- **Red test:** drive the client logic with the server failing in a unit test; assert attempts per minute stay at the bound.
- **Not a finding:** a loop bounded by a cap the code proves.
