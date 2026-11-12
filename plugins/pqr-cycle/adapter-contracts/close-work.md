# adapter-contract — close-work

What a project's close-work adapter must hold. `bootstrap-project` writes it
from `templates/skills/close-work.SKILL.md.template` and the rule in
`references/universal/close-work/RULE.md`.

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

1. **Steps** — reuse the review's proof run for the same tree; the trim check
   (the project's command, or `trim_check.py` from pqr-cycle); rewrite the
   state document with pass or fail beside each command and HEAD.
2. **Document → subject** — which document owns what. One subject, one owner.
3. **When to bump the version.**

## Not in it

Counts in the state document; history (it is `git log`); a line per change.
