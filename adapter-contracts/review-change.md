# adapter-contract — review-change

Contract a local `review-change` adapter must provide.

## Required frontmatter

```yaml
---
name: review-change                       # or local name
extends: production-quality-ready::review-change@1.x
contract: ../../CONTRACTS.md
version: 1.1.0
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---
```

## Division of Responsibilities

1. **The Plugin's Universal `review-change` provides:**
   - The Universal Adversarial Matrix (7 mandatory axes: Concurrency/TOCTOU, Parameter Omission/Input Tampering, Multi-Tenant/Anti-IDOR, Webhook 500 Retries/Idempotency, Boundary Sanitization/XSS, Accessibility WCAG 2.2 AA, and Database Migration Immutability).
   - The fundamental rule: "Tests passing is necessary, but never sufficient".
   - The strict 4-step execution order (diff -> local invariants -> universal matrix -> proof commands).

2. **The Local Adapter provides:**
   - **This project's invariants**: Numbered, specific business and architecture invariants that this project paid for once (with concrete examples and error codes).
   - **Proof command**: The exact command-line invocation to run build, lint, typecheck, tests, and migration checks in this repository.
   - **Repository-specific parameters**: Concrete local details for any of the 7 universal axes (e.g. specific roles, geofence distances, VAT rates).
