---
name: close-work
description: "Run at the end of every session, after review-change, before commit: rewrite ESTADO.md ('one subject, one owner; reason stays, history goes') writing only what the code cannot say. Not for opening a session (start-work)."
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

## Write only what the code cannot say

The change itself is not described anywhere: the diff, the comments and
`git log` already say it. Written down is only:

- **state** — where the work is, what is next, what was not seen — in
  `ESTADO.md`, every time;
- **a non-obvious reason** — as a comment beside the code it explains;
- **a rule that ties two distant places** — as a test, when it can be one;
- **a measured fact about an external tool** — one line in the facts
  document;
- **a known defect nobody is fixing** — one line in the defects list.

A document that grows with every change is read by nobody and drifts from
the code. When a session ends with a document longer than it began, check
that each added line is one of the five.

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
| "I'll record the test count." | It is stale at the next commit. `ESTADO.md` says pass or fail beside the command; `git log` keeps the rest. |
| "History is useful context." | `git log` keeps it, for free and without drifting. |
| "I'll document this change." | The code and its comments are the documentation; a document takes only the five things above. |
| "I'll summarise and link." | A summary next to a link is a second copy. Keep the link; cut the summary. |

## Contract for the local adapter

Document→subject table for the project; proof command; rule on when to
bump version.

See `adapter-contracts/close-work.md`.
