# adapter-contract — start-work

Contract a local `start-work` adapter must provide.

## Required frontmatter

```yaml
---
name: <local-name>                        # not the plugin skill's name (POLICY §3.2)
extends: production-quality-ready:start-work
allowed-tools: Read Glob Grep Bash Edit Write
---
```

The adapter body names the contract it is judged under, never a copy or a version: `production-quality-ready/CONTRACTS.md` (POLICY Â§3.1).

## Required body sections

1. **Where the state is** — path to `ESTADO.md` (or equivalent).
2. **Proof command** — the command that confirms the tree is sound.
   Report pass or fail in the session; no count is stored in the
   adapter or in the state document.
3. **Places where code tends to repeat** — table or list.
4. **What is not reopened** — where the measured facts, the known
   defects and the closed decisions live.

## Optional sections

- Project layers (if not obvious from the structure).
- Specific conventions (names, language, formatting).

## What the adapter does NOT

- Rewrite the universal `start-work` rule.
- Duplicate other owners' rules (cite, don't copy).
- Assert facts about other projects — only about this one.
