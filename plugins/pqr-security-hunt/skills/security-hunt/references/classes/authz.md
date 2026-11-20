# Classes — authorisation inside a tenant

Owner: `security-hunt`. Card format and fields: see the head of
`isolation.md`.

### authz.authn-not-authz
- **Check:** `sec.access-control-default-deny`
- **Invariant:** each state-changing route checks the role the business rule names, not only that a session exists.
- **Where it hides:** routes guarded by "logged in" while siblings check a role; a guard that allows a list of roles copied from a looser route; a client-portal role reaching staff routes.
- **Red test:** the lowest role that has a session calls the route; assert refusal and no state change.
- **Not a finding:** a route the product deliberately opens to every role — the role matrix must say so.

### authz.parallel-path
- **Check:** `sec.access-control-default-deny`
- **Invariant:** every path to the same state change applies the same check.
- **Where it hides:** a bulk endpoint, an import, a background job, a webhook, a form action and an API route that all reach one write; the strictest path is the one reviewed.
- **Red test:** perform the forbidden change through the weaker path; assert refusal.
- **Not a finding:** a weaker path reachable only by a trusted internal caller the code proves internal.

### authz.mass-assignment
- **Check:** `sec.access-control-default-deny`
- **Invariant:** a caller cannot set a field its role may not set (role, owner, tenant, price, status, approval).
- **Where it hides:** a body spread into an update; a schema with `.passthrough()` or optional privileged fields; an update builder fed by `Object.keys(body)`.
- **Red test:** send the privileged field with a value the role may not set; assert it is ignored or refused.
- **Not a finding:** a field the schema strips, proven by reading the schema the route actually uses.

### authz.invitation-binding
- **Check:** `sec.access-control-default-deny`
- **Invariant:** an invitation, share link or one-time token grants exactly the role and resource it was issued for, once, to the identity it names.
- **Where it hides:** accept flows that take the role from the request; tokens not bound to the invited email; reuse after acceptance; a revoked invitation still accepted.
- **Red test:** accept a token with a different identity, a changed role, twice, or after revocation; assert each refused.
- **Not a finding:** a link the product defines as shareable by anyone holding it.

### authz.privilege-change-stale
- **Check:** `sec.session-integrity`
- **Invariant:** demotion, removal or deactivation takes effect on the next request of every live session of that user.
- **Where it hides:** role cached in the session or token; realtime connections that keep the role of the moment they opened.
- **Red test:** demote a user with a live session; replay a privileged request with the old cookie; assert refusal.
- **Not a finding:** a short-lived token whose expiry the threat model accepts as the revocation bound.

### authz.irreversible-unconfirmed
- **Check:** `sec.business-logic-abuse`
- **Invariant:** an irreversible action (purge, delete account, send to client, issue invoice) is bound to the principal, resource and confirmation that authorised it.
- **Where it hides:** confirmation checked in the UI only; a precondition (fresh backup, re-authentication) enforced on one path and not on its API twin.
- **Red test:** call the action directly without the precondition; assert refusal.
- **Not a finding:** a precondition the server enforces, cited at its line.

### authz.derived-copy
- **Check:** `sec.access-control-default-deny`
- **Invariant:** a value a permission gates stays gated in every copy of it — a total cached on a parent row, a snapshot, a denormalised column, an export, a list that selects the whole row.
- **Where it hides:** the detail route checks "may see finance" but the project row carries `fees_total_cents` and the list or header route returns the row whole; a snapshot or PDF built before the gate; a search index or notification body that copies the gated field.
- **Red test:** as a role without the permission, call every route that returns the parent row or its copies; assert the gated field is absent, not only the gated route refused.
- **Not a finding:** a copy the role matrix shows to that role on purpose, cited.
