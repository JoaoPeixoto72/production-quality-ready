# Classes — browser and realtime client

Owner: `security-hunt`. Card format and fields: see the head of
`isolation.md`.

### client.dom-script
- **Check:** `sec.input-validated`
- **Invariant:** text another user controls never reaches a DOM sink that executes it.
- **Where it hides:** raw-HTML rendering of names, notes, chat messages, notification bodies; URLs placed in `href` without a scheme check (`javascript:`); SVG inlined from uploads.
- **Red test:** render the component with the hostile value (component or SSR test); assert the output contains no executable markup or scheme.
- **Not a finding:** a strict CSP that blocks inline script — still a defect, but it changes severity; record the CSP line.

### client.cross-site-socket
- **Check:** `sec.session-integrity`
- **Invariant:** a cookie-authenticated WebSocket upgrade is refused from a foreign origin.
- **Where it hides:** upgrade handlers that check the session but not `Origin`; a proxy that forwards the upgrade without the check.
- **Red test:** send the upgrade with the victim's cookie and a foreign `Origin`; assert refusal.
- **Not a finding:** a socket authenticated by a token the page fetches same-origin, not by cookie.

### client.credentialed-cors
- **Check:** `sec.access-control-default-deny`
- **Invariant:** credentialed cross-origin reads are allowed only for named origins.
- **Where it hides:** reflecting `Origin` with `Access-Control-Allow-Credentials: true`; regex allowlists that match suffixes; `null` origin allowed.
- **Red test:** request with a foreign and a `null` origin; assert no allow-origin echo with credentials.
- **Not a finding:** wildcard CORS on a route without credentials and without private data.

### client.private-cache
- **Check:** `sec.data-at-rest`
- **Invariant:** a response with private data is not stored by a shared cache.
- **Where it hides:** missing `Cache-Control: private, no-store` on authenticated responses; a CDN rule caching by path; a service worker caching API responses across users.
- **Red test:** request a private route; assert the cache headers forbid shared storage.
- **Not a finding:** a private response whose platform never caches dynamic responses, cited.

### client.framing
- **Check:** `sec.csp-strict`
- **Invariant:** pages with state-changing controls cannot be framed by another origin.
- **Where it hides:** no `frame-ancestors` (or `X-Frame-Options`) on HTML responses, only on JSON ones.
- **Red test:** request an HTML page; assert `frame-ancestors 'none'` or `'self'`.
- **Not a finding:** a page with no action and no private data.
