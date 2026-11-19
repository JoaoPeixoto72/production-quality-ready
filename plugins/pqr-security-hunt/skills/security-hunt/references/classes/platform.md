# Classes — secrets, errors, crypto and the platform

Owner: `security-hunt`. Card format and fields: see the head of
`isolation.md`.

### platform.internal-trust
- **Check:** `sec.access-control-default-deny`
- **Invariant:** a request is trusted as internal only when the platform proves it (a private binding, a signed header), never by a hostname, path prefix or header the client can send.
- **Where it hides:** `x-user-id`, `x-tenant`, `x-internal` headers set by a front service and accepted by the back service even when the client sets them; an internal hostname reachable from outside; a proxy that copies every client header.
- **Red test:** send the trusted header from outside (through the public proxy path in a fixture); assert it is stripped or refused.
- **Not a finding:** a header the proxy overwrites on every request, cited.

### platform.secret-exposure
- **Check:** `sec.data-at-rest`
- **Invariant:** secrets and other tenants' data never reach a client bundle, SSR payload, log line or error body.
- **Where it hides:** environment variables with a public prefix; server load functions returning whole rows (password hash, tokens, keys); logs printing request bodies or headers; error handlers echoing the exception.
- **Red test:** call the route or render the page; assert the payload contains none of the seeded secret values.
- **Not a finding:** a value designed to be public (a publishable key).

### platform.error-leak
- **Check:** `sec.errors-no-leak`
- **Invariant:** a production error answers with a generic body and a correlation id; stack traces, SQL and paths stay in the log.
- **Where it hides:** a default error handler in one router; validation errors that echo internal field names or other rows; database constraint messages passed through.
- **Red test:** trigger the error (bad id format, constraint violation); assert the body has no stack, SQL or path.
- **Not a finding:** a validation message that only names the caller's own input.

### platform.crypto-misuse
- **Check:** `sec.crypto-primitives-justified`
- **Invariant:** security values come from a CSPRNG; secrets are compared in constant time; encryption is authenticated with unique nonces; a crypto failure refuses.
- **Where it hides:** `Math.random` or time-based ids used as tokens; `===` on HMACs; AES without a tag or with a fixed IV; a verify that returns true on exception.
- **Red test:** a unit test on the primitive wrapper: two tokens differ in entropy source, tampered ciphertext is refused, verify on a malformed input refuses.
- **Not a finding:** a non-security id generated with a weak source.

### platform.debug-surface
- **Check:** `sec.api-surface-declared`
- **Invariant:** debug, seed, test and health-detail routes are absent from the production build or refuse every caller.
- **Where it hides:** routes gated by an environment flag the production config sets by default; a seed endpoint left behind; a status route returning config.
- **Red test:** call the route under the production configuration; assert not-found.
- **Not a finding:** a health route returning only "ok".
