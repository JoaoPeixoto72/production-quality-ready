# Project vocabulary and decisions — where they live

Reference for `spec`, `grill`, `slice`, `map` and `triage`. It says where a
settled word and a settled decision are written so the next agent finds them,
without a glossary file or a decision-record folder that grows with every
change (`PURPOSE.md §3.5`).

## Why it earns its place

An agent that invents a name for a concept the project already named produces
code that reads like a second codebase. An agent that re-argues a settled
decision spends a session to reach the same place. Both are fixed by writing
the word and the reason where the agent already looks: the code, and the
project's agent map (`AGENTS.md` / `CLAUDE.md`).

## A word

**The identifier is the definition.** One concept, one name, used the same in
the type, the function, the route and the message. Sharpen a fuzzy word at the
moment it is used: when someone says "account" and the code has both `Account`
(billing) and `User` (identity), ask which one, and use that name.

- **The negative matters.** When two neighbours are easy to confuse, the doc
  comment on the type says what it is *not*: "An `Order` exists before payment;
  a `Purchase` only after the money is captured."
- **One table, only where the names differ.** When the same thing carries a
  different name per layer (the window calls it `share`, the job kind is
  `convert`, the folder is `media/`), the agent map holds one table of those
  names. Nothing else goes there — a term the code names once needs no entry.
- Change the word in the same sitting as the discussion that changed it: a
  rename, not a todo.

## A decision

**The reason sits beside the code that enforces it.** "We chose X" is visible in
the code; "because Y would cost Z" is not — that is the comment.

- A decision that binds two distant places is a **test** when it can be one:
  the test fails the day someone breaks it, which a paragraph never does.
- A decision that shapes the whole project, and has no single line to sit
  beside, is **one line** in the agent map's list of what is not reopened: the
  decision and its reason, in the present tense.
- A later decision **replaces** the line; it does not append a new one. What was
  decided before is `git log`.
- Offer this only for a choice that is expensive to reverse. A choice between
  two equal options is not a decision worth recording.

## How the owners use them

- `grill` challenges a fuzzy word when the frontier question uses it, and
  settles it into the code's name.
- `spec` writes criteria in the code's words, and names the closed decisions its
  change must respect.
- `slice` and `map` name slices and tickets in the same vocabulary.
- `triage` reads an incoming request by concept, so the redundancy search finds
  the implementation the reporter could not name.
- `close-work` puts a reason beside the code, a cross-place rule in a test, and
  a project-wide decision in the agent map; it never copies them into the state
  document.
