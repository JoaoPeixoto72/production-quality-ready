# adapter-contract — verify

What a project's verify adapter must hold. `bootstrap-project` writes it from
`templates/skills/verify.local.SKILL.md.template` and the rule in
`references/universal/verify/RULE.md`.

## Frontmatter

```yaml
---
name: <local-name>        # its own name, never the rule's (start-work, review-change…)
description: "…"          # ≤ 250 characters, says when to use it and when not
allowed-tools: …
---
```

Nothing else: no `extends:`, no `contract:`. No host implements them, and the
adapter must work with the plugin not installed — that is the point of it.

## Self-contained

The adapter carries every step it needs, in the project's words. It cites a
project file by path; it never asks the reader to load a plugin skill to make
sense of it. It never copies what the agent map (`CLAUDE.md`/`AGENTS.md`)
already says — that file is always in context; the adapter points at its
section.

## Required sections

1. **Launch** — the command, and a check that what runs is newer than the
   sources.
2. **Surfaces worth proving** — routes, screens, endpoints.
3. **Test credentials** — names and where they live; never production secrets.
4. **Artefacts the app writes** — local DB, object store, logs.
5. **Traps** — this project's only; the desktop window harness is
   `drive-app-window` (pqr-desktop).

## Not in it

What to verify semantically — that is the change's spec and the owners.
