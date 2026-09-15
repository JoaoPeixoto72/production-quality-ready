---
name: start-work
description: "Open a work session on a project. Read the state, confirm the tree is sound (build, tests), find the owner before writing, avoid duplication. Universal contract; each project supplies a local adapter with its paths and commands. Use at the start of every conversation, and again mid-session before writing new code. Do NOT use to review written code — that's review-change. Do NOT use to close and update documents — that's close-work."
contract: CONTRACTS.md
evidence-schema: "1.3.x"
requires-adapter: true
adapter-contract: adapter-contracts/start-work.md
version: 1.0.0
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
   lives.
2. **Confirm the tree is sound.** Run the project's proof command
   (build + tests). Every reported number carries the command that
   produced it and the HEAD hash.
3. **Look up documents of decisions / facts / audits.** The adapter lists
   them.
4. **Search for the owner** of the subject about to change.
5. **Only then write.**

## Contract for the local adapter

The adapter is a local skill in the project's repo that:

- names the state file (path);
- gives the exact proof command (with the format for numbers);
- lists places where code tends to repeat in this project;
- lists documents of decisions/facts/audits that must not be reopened.

See `adapter-contracts/start-work.md` for the required frontmatter and
sections.
