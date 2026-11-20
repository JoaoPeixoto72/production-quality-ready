# Classes — authentication and session

Owner: `security-hunt`. Card format and fields: see the head of
`isolation.md`.

### auth.enumeration
- **Check:** `sec.auth-strength`
- **Invariant:** login, reset, invite and sign-up answer the same way, in the same time order, for a known and an unknown identity.
- **Where it hides:** a different status, message, redirect or response size; skipping the password hash on an unknown email; reset that says "sent" only for existing accounts.
- **Red test:** the same request for a known and an unknown identity; assert identical status and body.
- **Not a finding:** a timing difference below what the threat model accepts, measured, not guessed.

### auth.limiter-bypass
- **Check:** `sec.auth-strength`
- **Invariant:** the attempt limiter and the lockout key on a value the attacker cannot choose.
- **Where it hides:** the client IP read from a header the client sets (`x-forwarded-for`, `cf-connecting-ip` forwarded unverified across an internal hop); a limiter that skips requests with no IP; a lockout keyed on a normalisable email (case, dots, plus).
- **Red test:** vary the spoofable header or the email form across attempts; assert the limit still trips.
- **Not a finding:** a header the edge overwrites, when the source shows the internal hop cannot be reached from outside.

### auth.reset-token
- **Check:** `sec.auth-strength`
- **Invariant:** a reset or magic-link token is random, single-use, short-lived, bound to one account, stored hashed, and invalidated by use and by password change.
- **Where it hides:** comparison on the raw token; tokens never marked used; an older token still valid after a newer one is issued; reset that does not revoke sessions.
- **Red test:** use a token twice, after expiry, or on another account; assert refusal.
- **Not a finding:** a token property the code proves (expiry column checked in the query).

### auth.mfa-downgrade
- **Check:** `sec.auth-strength`
- **Invariant:** with MFA enrolled, no path yields a full session without the second factor; disabling MFA or reading recovery codes needs re-authentication.
- **Where it hides:** the intermediate "password ok" token accepted by full-session routes; an alternate login path (invite accept, reset, OAuth) that skips the second step; recovery codes reusable.
- **Red test:** with the step-one token only, call a full-session route; assert refusal. Reuse a recovery code; assert refusal.
- **Not a finding:** an alternate path the threat model routes through MFA, cited.

### auth.session-lifecycle
- **Check:** `sec.session-integrity`
- **Invariant:** logout, password change and email change revoke the sessions they should; a session id is issued anew on login.
- **Where it hides:** logout that only clears the cookie; password change that leaves other sessions alive; a session id accepted from the request before login.
- **Red test:** log out (or change password), replay the old cookie; assert refusal.
- **Not a finding:** a product decision to keep other devices signed in, written in the threat model.

### auth.cookie-and-csrf
- **Check:** `sec.session-integrity`
- **Invariant:** the session cookie is `HttpOnly`, `Secure`, scoped narrowly, and every cookie-authenticated state change is protected against cross-site requests.
- **Where it hides:** a state change on `GET`; a CSRF check skipped for one content type, one router, or requests without `Origin`; a second cookie set without the flags.
- **Red test:** send the state change cross-site (foreign `Origin`, form content type, or no `Origin`) with the session cookie; assert refusal.
- **Not a finding:** a missing flag on a cookie that holds nothing sensitive — trace what it carries first.
