---
name: close-work
description: "Run at the end of every session, after review-change, before commit: rewrite ESTADO.md ('one subject, one owner; reason stays, history goes') and record proof numbers with command and HEAD. Not for opening a session (start-work)."
contract: CONTRACTS.md
requires-adapter: true
adapter-contract: adapter-contracts/close-work.md
platforms: [web, desktop]
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

1. Verify before writing (the adapter says what to run). A test that
   failed or did not run goes into `ESTADO.md` as such, with the output.
2. Route the work through the owners (the adapter has the
   document→subject table).
3. Delete what stopped being true.
4. Rewrite `ESTADO.md`.
5. Read what you wrote, looking for duplication.
6. Close (commit; pipeline if applicable).

## Rationalisations that do not pass

| Excuse | Answer |
|---|---|
| "The document is basically right." | Basically right is wrong with confidence — the next conversation can't tell which part. |
| "I'll update `ESTADO.md` next time." | Next time has no memory of this one. |
| "I remember the number." | A number without its command and HEAD doesn't go in. Run it. |
| "History is useful context." | `git log` keeps it, for free and without drifting. |
| "I'll summarise and link." | A summary next to a link is a second copy. Keep the link; cut the summary. |

## Contract for the local adapter

Document→subject table for the project; proof command; rule on when to
bump version.

See `adapter-contracts/close-work.md`.
