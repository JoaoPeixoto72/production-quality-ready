# adapter-contract — review-change

Contract a local `review-change` adapter must provide.

## Required frontmatter

```yaml
---
name: review-change
extends: production-quality-ready::review-change@2.x
contract: ../CONTRACTS.md.snapshot
version: 2.0.0
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---
```

## Division of responsibilities

1. **The plugin's universal `review-change` provides:**
   - The adversarial matrix, axes tagged `both` / `web` / `desktop`
     (A1–A11), each citing its owner.
   - The founding rule: green tests are the minimum, never the approval.
   - The 5-step order: diff → local invariants → matrix → proof commands → verdict.

2. **The local adapter provides:**
   - `## Platform` — one line: `platform: web | desktop | both` (copied
     from `gates.json`) and the resulting list of axes that apply.
   - `## This project's invariants` — numbered; each with the concrete
     incident, decision or error code that motivated it. These are the
     things the project paid for once and must not pay for again.
   - `## Proof commands` — exact commands in order (build, typecheck,
     lint, tests, migrations). No counts in the adapter — counts live in
     `ESTADO.md` (or the project's state document).
   - Optional `## Project axes` (A12+), same shape as the universal ones.
   - Optional `## Where to look` — table of concrete files per axis
     (e.g. "A3 → `src/routes/tenant.ts` `tenantFromToken`").

## What the adapter must NOT do

- Re-copy the universal axis text. Cite the axis id.
- Store measured numbers (asserts, migrations). They go stale; state
  documents own them.
- Reference documents that do not exist in the repo.
