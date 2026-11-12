# adapter-contract — ship

What a project's ship adapter must hold. Deploy is the most project-specific
step there is: the order of migrations and code, who runs it, how it is undone.
The process skill `ship` (pqr-process) holds the generic rule — verified in
production, reversible before it starts — and reads these facts from the
adapter. `bootstrap-project` writes it from
`templates/skills/ship.SKILL.md.template`.

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

1. **How it deploys** — the command, or the pipeline that runs it (and on what
   event); where it runs from; what an agent may and may not run.
2. **Order** — e.g. migrations before code, API before web; what breaks if the
   order is swapped.
3. **After deploy** — the smoke test against production, and where its result
   is read.
4. **Roll back** — the one step that restores the previous version, and what it
   does not undo (a migration is forward-only).
5. **Needs a person** — the steps that wait for an explicit go-ahead.

## Not in it

Secrets or tokens; counts; history of past deploys.
