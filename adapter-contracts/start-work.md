# adapter-contract — start-work

Contract a local `start-work` adapter must provide.

## Required frontmatter

```yaml
---
name: start-work                          # or local name
extends: production-quality-ready::start-work@2.x
contract: ../CONTRACTS.md.snapshot              # relative to target repo root
version: 1.0.0
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---
```

## Required body sections

1. **Where the state is** — path to `ESTADO.md` (or equivalent).
2. **Proof command** — the command that confirms the tree is sound.
   Format: `<command>` (which HEAD, how many tests) — every number with
   its command alongside.
3. **Places where code tends to repeat** — table or list.
4. **Documents of decisions/facts/audits** — where not to reopen.

## Optional sections

- Project layers (if not obvious from the structure).
- Specific conventions (names, language, formatting).

## What the adapter does NOT

- Rewrite the universal `start-work` rule.
- Duplicate other owners' rules (cite, don't copy).
- Assert facts about other projects — only about this one.
