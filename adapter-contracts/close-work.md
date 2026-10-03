# adapter-contract — close-work

Contract a local `close-work` adapter must provide.

## Required frontmatter

```yaml
---
name: <local-name>                        # not the plugin skill's name (POLICY §3.2)
extends: production-quality-ready:close-work
contract: production-quality-ready/CONTRACTS.md
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---
```

## Required body sections

1. **Document → subject table** — which document owns what in the
   project. Rule "one subject, one owner" applied here.
2. **`ESTADO.md` structure** — if it differs from the universal fixed
   structure.
3. **Pre-commit proof command** — including
   `skills/close-work/scripts/trim_check.py`, which must pass.
4. **When to bump version** — when a task earns a version, when it
   doesn't.

## What the adapter does NOT

- Rewrite the "reason stays, history goes" rule.
- Duplicate other project documents (points at them).
- Store counts, or route a line to a document for every change — the
  table says where the five kinds of lost-if-unwritten fact go, nothing
  more.
