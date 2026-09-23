---
name: start-work
description: "Run at the start of every conversation and before new code: read the state document, confirm build and tests at HEAD, name the canonical owner of the code about to change, prevent duplication. Not for review or close (close-work)."
contract: CONTRACTS.md
evidence-schema: "1.3.x"
requires-adapter: true
adapter-contract: adapter-contracts/start-work.md
platforms: [web, desktop]
version: 2.1.0
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---

# start-work

Universal contract for opening a work session. **Every conversation is
born without memory**, and that makes it always cheaper to rewrite than
to discover what already exists — this skill is the three minutes that
sit between that state and yet another copy of the same code.

## Founding rule: find the owner before writing

There is one owner per subject in the codebase. Before writing anything,
identify who — file, module, function — already owns it. If nothing owns
it, write; if something does, extend or delegate. A new copy is a
defect, not a shortcut.

## Order

1. **Read the state.** The adapter says where `ESTADO.md` (or equivalent)
   lives, and which part of it decides anything.
2. **Confirm the tree is sound.** Run the project's proof command
   (build + tests). Every reported number carries the command that
   produced it and the HEAD hash. A red baseline is reported before any
   new work — otherwise the next failure has no owner.
3. **Look up documents of decisions / facts / audits.** The adapter lists
   them.
4. **Search for the owner** of the subject about to change.
5. **If the task is a bug, reproduce it first** — a command, a test, or
   the steps in the running app that show it. A bug nobody reproduced
   cannot be proven fixed.
6. **Only then write.**

## Rationalisations that do not pass

| Excuse | Answer |
|---|---|
| "I know where this lives." | The conversation has no memory; search anyway. It takes a `grep`. |
| "Writing it fresh is faster." | Faster today, a second owner forever. Extend the one that exists. |
| "Tests were green last session." | Last session is not HEAD. Run the baseline. |
| "The bug is obvious, no need to reproduce." | Then reproducing is cheap. Without it, "fixed" is an opinion. |

## Contract for the local adapter

The adapter is a local skill in the project's repo that:

- names the state file (path);
- gives the exact proof command (with the format for numbers);
- lists places where code tends to repeat in this project;
- lists documents of decisions/facts/audits that must not be reopened.

See `adapter-contracts/start-work.md` for the required frontmatter and
sections.
