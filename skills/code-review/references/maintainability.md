# Maintainability — what code-review looks for

## Contents

- 1. Budgets (measured)
- 2. Review (the M axes)
- 3. How to report

Owner: `code-review`. Cited by `review-change` (axes M1–M7).

**Rule: code another person can change on their own.** Half
of it is measured against budgets; the other half is reviewed, because no
number sees it.

Distilled from the reviewers most used with Claude Code — Anthropic's
`code-review` and `pr-review-toolkit`, Cursor's
`thermo-nuclear-code-quality-review`, `addyosmani/agent-skills`
`code-simplification` — and kept to what survives contact with a real
repository.

## 1. Budgets (measured)

Declared by the project in `<host>/gates.json` →
`owners.code-review.budgets`; measured by `scripts/quality_scan.py`.

| Budget | Default | Where the default comes from |
|---|---|---|
| `file-lines` | 1000 | Cursor and Addy both block a change that pushes a file past ~1k lines |
| `function-lines` | 50 | ESLint `max-lines-per-function`; Addy's "long functions (50+)" |
| `nesting` | 3 | Addy's "deep nesting (3+ levels)"; ESLint `max-depth` is 4 |
| `params` | 4 | between ESLint `max-params` (3) and Clippy `too_many_arguments` (7) |

**Defaults, not standards.** The project's numbers win, and a project that
declares none gets `quality.budgets-declared: FAIL` (LOW) — the numbers
are a decision, and someone should have made it.

**Ratchet, not amnesty.** `quality_scan.py --write-baseline` records
today's debts in `<host>/quality-baseline.json` (committed). A recorded
debt passes while it does not grow; a new one, or a grown one, fails.
Touching an 800-line component is allowed; making it 810 is not — extract
first.

**A linter with the same numbers is a better instrument.** When the
project already runs one, cite its command instead:

| Stack | Rules |
|---|---|
| ESLint | `max-lines`, `max-lines-per-function`, `max-depth`, `max-params`, `complexity`, `no-magic-numbers`, `react/forbid-dom-props` (`style`) |
| Clippy (`clippy.toml`) | `too-many-lines-threshold`, `too-many-arguments-threshold`, `cognitive-complexity-threshold` |
| Ruff | `C901`, `PLR0913`, `PLR0915`, `PLR2004` |

## 2. Review (the M axes)

What the budgets cannot see. Each axis has the question to ask and the
move to propose — a finding without a move is half a finding.

**M1 · Size and shape.** Does the change grow a function or file that is
already over budget, or push one across it? → Split first, in its own
commit: extract a pure helper, a sub-component, a module with one door.

**M2 · Spaghetti growth.** A new `if` bolted onto an unrelated flow; the
same `kind === "x"` check in three files; feature logic inside a shared
module; logic in the wrong layer. → Repeated conditionals are a missing
model: a type, a table, a strategy. Move the feature behind its own
boundary.

**M3 · Duplication.** Does this already exist — a helper, a hook, a
utility the project owns (`start-work` names the owners)? → Reuse it.
Extract on the third copy, not on a guess about the second.

**M4 · Named values, no inline decisions.** A literal that carries a
decision — timeout, limit, retry count, colour, spacing, a user-visible
string — gets a name in one place: a constant, a design token (CSS custom
property), an i18n key. Styles go through classes and tokens; an inline
`style` is only for a value computed at runtime, passed as a custom
property (`style={{ "--progress": pct }}`). `ui-system`'s `audit_ui.py`
flags `inline-style` and remote fonts.

*What M4 is not:* a variable for every expression. A name for a value used
once and obvious where it sits is a hop without meaning; `0`, `1`, `-1`,
`""` and an index need no name. Name a condition when its meaning is not
obvious at a glance (`const expired = now > deadline + grace`).

**M5 · Indirection earns its keep.** Thin wrappers and pass-through
helpers; an abstraction "we might need"; a boolean parameter that makes a
function do two things (→ two functions); nested ternaries; a clever
one-liner that needs a pause to read. Fewer lines is not the goal —
fewer concepts the reader must hold is.

**M6 · Errors are not swallowed.** Empty `catch`; a catch-all that logs
and carries on; `.ok()`, `let _ =`, `unwrap_or_default()` on a result that
matters; `?.` hiding an operation that failed; a fallback that masks the
cause. → Handle it, propagate it, or write the reason it is safe to drop.

**M7 · Comments and types say the truth.** A comment says *why*; one that
restates the line, or that the code no longer honours, goes — check every
claim a comment makes against the code under it. At boundaries, types are
explicit: no `any`, a cast only with its reason, an optional only when
absence means something.

## 3. How to report

- **High signal only.** Every finding has `path:line`, the axis, and the
  move. Taste is not a finding.
- **What the linter catches belongs to the linter.** Don't repeat it by
  hand; make sure it runs.
- **The diff, not the archaeology.** Pre-existing debt is reported only
  when the change touches it (that is what the baseline is for).
- **Structure before nits.** When a structural problem exists, lead with
  it; a list of nits buries it.
- **Refactor and behaviour change never share a commit.** A refactor
  that needs a test changed was a behaviour change.
