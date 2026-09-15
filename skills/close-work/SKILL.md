---
name: close-work
description: "Update the project's documents at the end of a work session. Says which document owns which subject (rule \"one subject, one owner\"), separates reason (stays), proof (stays in verified-facts), history (goes). Rewrites ESTADO.md. Universal contract; each project supplies the adapter with its document table. Use at the end of every work session, before commit. Do NOT use to open — that's start-work. Do NOT use to review code — that's review-change (comes first)."
contract: CONTRACTS.md
evidence-schema: "1.3.x"
requires-adapter: true
adapter-contract: adapter-contracts/close-work.md
version: 1.0.0
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---

# close-work

Universal contract for closing a work session. **The next conversation
only knows what is written** — if the document is out of date, it doesn't
end up without information: it ends up with wrong information, which is
worse.

## Founding rule: one subject, one owner

Each document owns one subject and writes about only that. If it needs
another, **it links, not copies** — two copies drift, and once they do
there's no way to know which is right.

## Reason stays, proof stays, history goes

- **Reason** — *stays*. Why it is this way, and what breaks if it
  changes.
- **Proof** — *stays*, and only in the project's "verified facts"
  document.
- **History** — *goes*. When it was done, in which version it appeared,
  what was there before.

Phrases that are always history: "in 0.2.1 this was fixed", "used to
be", "resolved on <date>", "what was here no longer applies". A document
describes the present.

## ESTADO.md always rewrites itself

Fixed structure (the adapter says where it lives):

1. **Where we are** — version, what compiles and passes, what has been
   built.
2. **Next** — concrete next step, with the first move already written.
3. **Waiting on another machine, or on money.**
4. **To eyeball manually** — what no test catches.
5. **Ideas, for gain** — none promised to anyone.

## Order

1. Verify before writing (the adapter says what to run).
2. Route the work through the owners (the adapter has the
   document→subject table).
3. Delete what stopped being true.
4. Rewrite `ESTADO.md`.
5. Read what you wrote, looking for duplication.
6. Close (commit; pipeline if applicable).

## Contract for the local adapter

Document→subject table for the project; proof command; rule on when to
bump version.

See `adapter-contracts/close-work.md`.
