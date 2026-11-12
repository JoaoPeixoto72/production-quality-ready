
# start-work — the rule

The rule a project's start-work adapter is written from. It is not a skill:
`bootstrap-project` turns it into the project's own, self-contained skill
(`adapter-contracts/start-work.md`), so the cycle works with no plugin loaded.

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
2. **Confirm the tree is sound — when the task changes code.** A question
   needs no baseline. A change runs the project's cheapest sound-tree
   command (a status or typecheck command), reported pass or fail beside it;
   the full suite runs once, at review. A red baseline is reported before
   new work — otherwise the next failure has no owner.
3. **Look up what is not reopened** — the measured facts, the known
   defects and the closed decisions the adapter points at.
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
| "Tests were green last session." | Last session is not HEAD. Run the baseline before changing code. |
| "The bug is obvious, no need to reproduce." | Then reproducing is cheap. Without it, "fixed" is an opinion. |

## The project's adapter

It names the state file, the baseline command, the places where code tends
to repeat and the documents that are not reopened. Shape:
`adapter-contracts/start-work.md`.
