# adapter-contract — review-change

Contract a local `review-change` adapter must provide.

## Required frontmatter

```yaml
---
name: review-change                       # or local name
extends: production-quality-ready::review-change@1.x
contract: ../../CONTRACTS.md
version: 1.0.0
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---
```

## Required body sections

1. **This project's invariants** — enumerated, each with the example
   that motivated it. Not generic best practices.
2. **Proof command** — what runs before closing. With number + HEAD.
3. **What the adapter does NOT cover** — cross-references to the plugin
   owners that own similar rules.

## What the adapter does NOT

- Write UX/a11y rules — cite `design-pro`.
- Write IPC/API contract rules — cite `code-review-contract`.
- Write security rules — cite `security-audit`.
- Write performance rules — cite `performance-audit`.
- Write **only** the invariants that belong to this project, with the
  example that motivated them.
