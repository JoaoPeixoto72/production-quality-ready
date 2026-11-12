# adapter-contract — start-work

What a project's start-work adapter must hold. `bootstrap-project` writes it
from `templates/skills/start-work.SKILL.md.template` and the rule in
`references/universal/start-work/RULE.md`.

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

1. **Steps** — read the state document (path, which sections decide); a
   baseline only when the task changes code, and the cheapest one the project
   has (a status or typecheck command), reported pass or fail; find the owner;
   reproduce a bug first. The full proof runs once, at review.
2. **Where code tends to repeat** — table or list.
3. **What is not reopened** — where measured facts, known defects and closed
   decisions live.

## Not in it

Counts; facts about other projects; a second copy of a rule the agent map holds.
