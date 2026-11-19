# Classes — untrusted input to a dangerous sink

Owner: `security-hunt`. Card format and fields: see the head of
`isolation.md`.

### input.query-injection
- **Check:** `sec.input-validated`
- **Invariant:** caller data reaches a query only as a bound parameter, including identifiers (sort column, field name, table).
- **Where it hides:** string-built `ORDER BY`, `IN (...)` lists, dynamic column names, search patterns; a helper that interpolates "safe" values.
- **Red test:** send a value that changes the query's meaning (a quote, a column name, a `LIKE` wildcard) and assert the result set or the error matches the parameterised behaviour.
- **Not a finding:** an interpolated value proven to come from a closed allowlist in code.

### input.markup-injection
- **Check:** `sec.input-validated`
- **Invariant:** caller text is escaped for the context it is rendered in — HTML page, email HTML, PDF HTML, attribute, URL, CSV cell.
- **Where it hides:** raw-HTML rendering (`{@html}`, `innerHTML`, `v-html`, `dangerouslySetInnerHTML`); email and PDF templates built by string concatenation; Markdown rendered without a sanitiser; CSV exports starting with `=`.
- **Red test:** store a value with markup in the field; render through the sink; assert the output contains the escaped form.
- **Not a finding:** a field only staff of the same tenant can write and only they read, when the threat model treats staff as trusted — say so.

### input.second-order
- **Check:** `sec.input-validated`
- **Invariant:** data validated on the way in is re-validated where a later context gives it new meaning (path, URL, regex, template, header, policy).
- **Where it hides:** a slug that becomes a storage key; a stored URL fetched later; a name placed into `Content-Disposition` or an email header.
- **Red test:** store the value through the normal write; trigger the later use; assert the sink receives the neutralised form.
- **Not a finding:** a later use the code re-validates, cited.

### input.server-fetch
- **Check:** `sec.input-validated`
- **Invariant:** a URL the server fetches on a caller's behalf is restricted to the destinations the feature needs, after redirects.
- **Where it hides:** webhooks, logo or avatar by URL, link previews, import from URL, PDF renderers loading remote assets.
- **Red test:** point the feature at an internal or loopback address (in a local fixture); assert the request is refused before it is sent.
- **Not a finding:** a runtime that cannot reach internal addresses at all, proven by its documented network model and cited.

### input.redirect
- **Check:** `sec.input-validated`
- **Invariant:** a redirect target from the request is a relative path or an allowlisted origin.
- **Where it hides:** `next`, `return`, `redirect`, `url` parameters after login, logout, OAuth or invitation; `//evil` and `/\evil` forms.
- **Red test:** send an external and a scheme-relative target; assert the response redirects inside the app.
- **Not a finding:** a redirect target taken from server state only.

### input.upload
- **Check:** `sec.file-uploads-safe`
- **Invariant:** an uploaded file is typed by its bytes, bounded in size before it is buffered, named by the server, and served as an attachment unless its type is on an inline allowlist.
- **Where it hides:** trusting the declared MIME or the extension; SVG or HTML served inline from the app origin; the original filename used in a key or header; size checked after reading the whole body.
- **Red test:** upload HTML or SVG with an image MIME, then fetch it; assert it is refused or served as an attachment with a safe type.
- **Not a finding:** a type served inline that the allowlist names and the bytes match.
