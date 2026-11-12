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
- **History** — a line that tells how the text came to be ("used to",
  "since 3.2", "was fixed"). `git log` keeps it; the document says the
  present (`PURPOSE.md §3.5`).

## In this plugin

- `description` ≤ 250 chars, starts with an action verb, names when it
  runs, and names the sibling that owns the case it refuses
  (`POLICY.md §1.2`).
- Frontmatter carries only the [Agent Skills](https://agentskills.io)
  spec fields (`name`, `description`, `allowed-tools`). Host-specific
  behaviour goes in the body or in a host file such as
  `agents/openai.yaml` — never a non-spec top-level key.
- The body carries the steps and the reference every branch needs. Detail
  for one branch goes to `references/`, `scripts/`, or the skill that owns
  it.
- Store no counts in a skill, an adapter or a state document: a count is
  stale at the next commit. A number that proves something lives in an
  evidence file, with its `command` and `log` (`CONTRACTS.md §4.6`).

## Report to the human

- **Redact before you show.** Commands, outputs and artefacts carry
  secrets: write `<REDACTED>` in their place, and build loops against
  environment variables so the credential never enters the transcript.
- **Cite the source.** A claim about the outside world names the file,
  the version or the URL it came from (`research`).
- **Re-pitch when it does not land.** If the person says the last
  message did not make sense, do not repeat it louder: give a line of
  context, then the same content in shorter sentences and the project's
  own vocabulary.
- **Say what you did, what you found, what you need.** Not the story of
  getting there.
