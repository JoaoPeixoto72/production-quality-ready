# Project vocabulary and decisions — GLOSSARY.md and ADRs

Reference for `spec`, `grill`, `slice`, `map` and `triage`. It holds how to
write the two documents that make an agent's language match the project's.

## Why it earns its place

An agent that invents a name for a concept the project already named produces
code that reads like a second codebase. A glossary costs a line per term and
removes that class of drift. A decision record costs a paragraph and stops the
same debate from being had twice.

## GLOSSARY.md

One term per entry, one meaning.

```markdown
## Order

A customer's intent to buy, before payment. Not to be confused with
**Purchase**, which exists only after the money is captured.

- Owner: `src/orders/`
- Used in: checkout, refunds, the billing webhook
```

Rules:

- **One term, one meaning.** Two meanings is two terms; name the second.
- **The negative matters.** Say what it is *not* confused with, naming the
  neighbour term. That line is what stops the drift.
- **Sharpen fuzzy words at the moment they are used**, not in a later cleanup:
  when someone says "account" and the project has both `Account` (billing) and
  `User` (identity), ask which one, and record the answer.
- **Point at the code** that owns the concept. A glossary entry with no owner
  is a wish.
- **Update it in the same sitting** as the discussion that changed a term — an
  inline edit, not a todo.

## ADRs

Offer one **sparingly**: only for a decision that is expensive to reverse and
whose reasoning will otherwise be lost. A choice between two equal options is
not an ADR; a choice that constrains the system for a year is.

```markdown
# 0007 — Tenant identity in the URL path, not a header

## Context
<what forced a decision>

## Decision
<what was decided>

## Consequences
<what becomes easy, what becomes hard, what is now forbidden>
```

Rules:

- Number them, sequentially, in one folder the project already uses
  (`docs/decisoes/`, `docs/adr/`, `adr/`).
- **The reasoning is the value**, not the decision: "we chose X" is visible in
  the code; "because Y would have cost Z" is not.
- Never edit a published ADR to reflect a later decision. Write a new one that
  supersedes it, and say so in one line.
- If a "decision" is really a convention, it belongs in the code's conventions
  document, not an ADR.

## How the owners use them

- `grill` challenges a fuzzy word when the frontier question uses it, and
  records the sharpened term.
- `spec` writes criteria in the glossary's words, and names the ADRs its change
  must respect.
- `slice` and `map` name slices and tickets in the same vocabulary.
- `triage` reads an incoming request by concept, so the redundancy search finds
  the implementation the reporter could not name.
- `close-work` routes a term or decision to whichever document owns it; it
  never copies the glossary into the state document.
