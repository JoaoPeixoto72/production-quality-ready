# adapter-contract — review-change

What a project's review adapter must hold. `bootstrap-project` writes it from
`templates/skills/review-change.SKILL.md.template` and the rule in
`references/universal/review-change/RULE.md`.

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

1. **Steps** — the eight of the rule: diff → spec axis → invariants → axes →
   maintainability → proof → argue against approval → verdict per axis.
2. **Invariants** — a pointer to the agent-map sections that hold them, never a
   copy. Only a project with no agent map lists them here, each with the
   incident that paid for it.
3. **Axes for the platform** — one line per applicable axis (A1–A11 of the
   rule, plus A12+ of the project): the scenario and what is required.
4. **Where to look** — the project's files per axis. This table is what makes
   the review proportional: an axis whose files the diff does not touch is
   listed in one line, not judged.
5. **Proof commands** — in order, run once per state of the tree (the key and
   `.work/proof.txt` of the template).

## Not in it

Counts; the full axis text of the rule; invariants the agent map already holds.
