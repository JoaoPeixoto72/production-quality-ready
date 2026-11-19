# Classes — tenant and object isolation

Owner: `security-hunt`. Read by a hunter whose unit names a class below, and
by the verifier of a candidate of that class.

Every card: the **invariant** the code must hold, **where** a break hides,
the **red test** that proves the break, and what is **not a finding**. A
card's `Check:` is the `security-audit` check a confirmed finding fails.

### iso.cross-tenant-id
- **Check:** `sec.tenant-isolation`
- **Invariant:** a resource addressed by id is read or written only when it belongs to the caller's tenant, decided from the session, never from the request.
- **Where it hides:** a query that filters by `id` alone; a lookup helper reused by a route that skips its scoped twin; a second route to the same row (detail vs. download vs. export vs. preview) where one path forgot the scope; `UPDATE`/`DELETE` scoped on the `SELECT` but not on the write.
- **Red test:** two tenants with dummy rows; tenant B's session requests tenant A's id on the exact route; assert `404` (or the project's not-found) and that A's row is unchanged.
- **Not a finding:** a route that returns `403` instead of `404` when the project's threat model accepts existence disclosure; a shared catalogue row that is global by design.

### iso.tenant-from-request
- **Check:** `sec.tenant-isolation`
- **Invariant:** the tenant scope comes from the authenticated principal only.
- **Where it hides:** `tenant_id`, `org`, `workspace` read from body, query, header or path and used in a query; a super-user impersonation parameter honoured for every role.
- **Red test:** tenant B's session sends tenant A's id in the field the handler reads; assert the write lands in B or is refused, and A is untouched.
- **Not a finding:** a super-user route whose guard is proven to admit only the super role.

### iso.foreign-parent
- **Check:** `sec.tenant-isolation`
- **Invariant:** a row may only reference parents of its own tenant.
- **Where it hides:** create/update accepting `project_id`, `client_id`, `member_id` and checking only that the parent exists; joins that later read the foreign parent's fields back to the attacker.
- **Red test:** tenant B creates a child pointing at A's parent id; assert refusal, and that no read of B's data returns A's parent fields.
- **Not a finding:** a database trigger or composite key already refuses it — cite it and close the unit.

### iso.derived-reader
- **Check:** `sec.tenant-isolation`
- **Invariant:** every reader derived from private data (search, listing, counts, export, notification, activity feed, PDF/email render, cache) applies the same scope as the primary read.
- **Where it hides:** global search unions; aggregate dashboards; notification fan-out by role instead of by tenant; a cache key without the tenant; an export job that takes ids from the request.
- **Red test:** seed a distinctive string in tenant A; as tenant B, exercise the derived reader; assert the string never appears.
- **Not a finding:** aggregate counts the product deliberately shows across tenants (public stats) — the threat model must say so.

### iso.realtime-room
- **Check:** `sec.tenant-isolation`
- **Invariant:** joining a realtime channel (WebSocket room, Durable Object, pub/sub topic) requires membership of the resource the channel represents, checked at join and on every privileged message.
- **Where it hides:** room ids derived from a client-supplied name or id (`idFromName(userInput)`); membership checked at upgrade but not after the member is removed; broadcast that includes presence or typing data of other tenants.
- **Red test:** as tenant B, open the channel for A's resource id; assert the upgrade is refused or no A message is delivered.
- **Not a finding:** a public broadcast channel the product defines as public.

### iso.object-key
- **Check:** `sec.tenant-isolation`
- **Invariant:** a stored object (blob, file, image, backup) is served only after the caller is authorised for the record that owns it.
- **Where it hides:** a download route keyed by storage key; a public URL whose key is guessable (sequential, derived from ids); a signed URL whose scope or expiry exceeds the record's; a "public" logo route that also serves other keys.
- **Red test:** as tenant B, request A's object by the route and the key format the code builds; assert not-found.
- **Not a finding:** an object the product publishes on purpose (a public logo) when the route can serve nothing else.

### iso.restore-authority
- **Check:** `sec.tenant-isolation`
- **Invariant:** import, restore, undelete and duplication apply the *current* owner, scope and validation — never the ones stored in the snapshot.
- **Where it hides:** restore that trusts `tenant_id` or `created_by` inside the snapshot; undelete that resurrects access revoked since; a template or factory copy that carries rows of another tenant.
- **Red test:** build a snapshot whose rows carry tenant A's id, restore it as tenant B; assert every restored row belongs to B and A is untouched.
- **Not a finding:** a super-user-only restore whose guard is proven.
