# writing-for-agents — how to write a skill, an adapter or a rule

Load this before writing or editing anything an agent reads: a `SKILL.md`,
an adapter, a file under `rules/`, `AGENTS.md`, a state document, a
reference.

## The pointer is the routing

A line that is always in context — a `description`, an `AGENTS.md` row — is
a **pointer**: it names material held out of context and encodes the
condition that reaches it. The pointer's wording, not its target, decides
when the agent gets there. A must-have document behind a weak pointer is a
variance bug: sharpen the wording first, and inline the material only if
sharpening fails.

- Front-load the leading word — the word the agent thinks with.
- One trigger per branch. A synonym that renames the same branch is one
  branch written twice.
- Cut identity the linked document already carries.

## Where each piece sits

Rank material by how soon the agent needs it: in-file steps, then in-file
reference, then disclosed reference behind a pointer. **Push behind a
pointer what only some branches reach; keep in the file what every branch
needs.** A skill that buries its steps under reference turns attention into
a coin flip.

Keep a concept's definition, rules and caveats under one heading, so
reading one part brings its neighbours. Repeating a meaning in two places
is duplication: one edit becomes nine, and the meaning reads as more
important than it is.

## Say the target, not the ban

Steering by prohibition drags the forbidden behaviour into context and
makes it more available. Write the positive target — "write one-line
comments" — so the banned one is never spoken. A ban earns its place only
as a hard guardrail that cannot be phrased positively, and it names the
target beside it. `anti-prompt-injection.md` is the plugin's one such
guardrail.

## Every step ends on a criterion

A step ends on a condition that says done. A vague bound ("understanding
reached") invites premature completion. Demand drives legwork: "every
modified route accounted for" forces thorough work where "produce a change
list" does not. The strongest criteria are both checkable and exhaustive.

## Prune by test, not by taste

- **No-op** — an instruction the agent already obeys by default pays load
  to say nothing. Delete the whole sentence, not words from it.
- **Cache** — a document that restates the manifests, the script list or
  the config goes stale; the environment is the source of truth for those
  facts. Keep what the agent cannot find by looking: the reason behind a
  choice, the unwritten convention, the gotcha no config confesses.
- **Sediment** — a line that no longer bears on the document's job. Removing
  it is the fix.

## In this plugin

- `description` ≤ 250 chars, starts with an action verb, names when it
  runs, and names the sibling that owns the case it refuses
  (`POLICY.md §1.2`).
- The body carries the steps and the reference every branch needs. Detail
  for one branch goes to `references/`, `scripts/`, or the skill that owns
  it.
- Every number comes from a command, with the command and the commit
  beside it (`CONTRACTS.md §4.6`).
