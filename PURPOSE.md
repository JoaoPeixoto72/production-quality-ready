# PURPOSE — what `production-quality-ready` is for

Orientation document. Read **before** evaluating the plugin. Answers one
question: *what does this exist for, and what counts as being well
made.*

Doesn't tell the story of how it was designed: the reason for a choice
sits beside the rule it explains, and the story is `git log`. The rules
live in `CONTRACTS.md` and `POLICY.md`.

---

## 1. The problem

**An app that works is not an app you can sell.** What sits between the
two is not a feature — it's a list of subjects nobody handled because
nobody owned them: there is no way to diagnose a customer from a
distance, nobody walked through installation on a clean machine, the
installer isn't signed, activation has never failed in testing because
it was never tested to fail, and accessibility is an opinion instead of
a number.

The agent working on the app has the same problem in miniature. Every
conversation is born without memory, and that makes it **always cheaper
to rewrite than to discover what already exists**. The waste accumulates
on its own: the same pattern copied in three places, three skills
checking contrast with three different criteria and none saying which
wins, and the audit engine — the thing that defines what counts as
proof — trapped inside a skill that serves only one repository.

This plugin is the answer to both at once.

---

## 2. What the plugin is

**A quality system built of independent owners**, installable in any
repository, that answers *"can this be sold?"* with demonstrated
defects, declared scope, and an honest list of what could not be
verified.

Every skill wakes when its `description` matches the task. None
invokes another.

| Block | Skills |
|---|---|
| Generator (run first) | `bootstrap-project` |
| Work cycle | `start-work`, `review-change`, `close-work` |
| Proof | `verify` (+ `drive-app-window` on desktop) |
| Audit owners | `code-review`, `security-audit`, `reliability-audit`, `design-pro`, `ui-system`, `release-audit`, `commercial-readiness`, `audit-website` |
| Orchestrator | `audit-app` |

15 skills; 14 owners of a subject plus one technical capability.

---

## 3. The five ideas holding it up

Everything else is a consequence of these. Anyone evaluating the plugin
is, at bottom, checking whether they hold in what is written.

### 3.1 One subject, one owner, one rule

Every subject has **exactly one** owner, and that owner declares the
**rule** — the criterion that decides `PASS`/`FAIL`, named and
versioned. Other owners may *cite* the rule; none rewrites it.

Contrast shows why: three owners with three criteria — WCAG 4.5:1, an
OKLCH ΔL heuristic, and a gate that decides sellability with no number
at all — give three answers to one question. That is not robustness; it
is having no answer.

### 3.2 One rule, multiple instruments

**The opposite of merging.** A subject has N independent instruments,
and an instrument never closes a verdict — it produces candidates.

Two instruments are only redundant when the universe of one is
contained in the other **and** the blind spot of the other is contained
in the first. Static ΔL over `tokens.css` is exhaustive over the
declared pairs and blind to runtime composition; pixel measurement is
truthful over what was rendered and blind to state nobody opened.
Neither contains the other, so **both stay**, each declaring its
universe and its blind spot.

Reducing instruments to keep the architecture pretty is losing
coverage.

### 3.3 Evidence is a file, not a call

A skill does not invoke another — a skill's body loads into current
context, and an orchestrator that "called" eleven owners would be the
monolith the design avoids.

Every owner writes
`.audit/<owner>/<producer>--<check>.evidence.yaml`. `audit-app` reads,
validates, aggregates and applies gates. Does not run commands against
the audited repo, does not invoke anyone, and running it twice gives
the same result.

Practical consequence that justifies the cost: **an owner can run
alone** — only `security-audit` on a nightly pipeline, without
dragging the rest.

### 3.4 Gate, never a score

A gate is binary. "94/100" opens nothing; an open `BLOCKER` closes.

And **absence is never approval**: an owner without evidence reports
`Coverage: BLOCKED (n/m)` — with the fraction, because `BLOCKED (0/8)`
and `BLOCKED (7/8)` are the same token but not the same knowledge
state. An owner missing from the project's `gates.json` is a defect of
the file, not "doesn't count": non-applicability is declared with an
auditable reason.

### 3.5 The code is the source; a document holds only what it cannot say

Documents drift and the code cannot lie about itself: a written recipe
("a tool touches six places") was wrong where one `git grep` found the
true ten. So the work cycle writes little, and in small pieces:

- **where** comes from searching the code, starting from something that
  already exists;
- **why** is a comment beside the line it explains — only when the code
  cannot say it and the next agent would undo the line without it; one
  line, never more than three. Its reader is an agent that reads it on
  every visit: a line it does not need costs tokens each time and drifts;
- **a rule between two distant places** is a test;
- **a document** holds only what no file can say — the state of the
  work, a measured fact about an external tool, a known defect nobody is
  fixing — plus the guides written for people;
- **history** is `git log`: a document describes the present, stores no
  counts, and never narrates how it got there;
- **files stay small**, one subject each, under the budgets
  `code-review` measures.

`close-work` applies this at the end of every session; the plugin applies
it to itself — it has no change log, only its commits.

---

## 4. The subjects, and each one's rule

This is the closed list. A subject not here has no owner, and that is
the defect to look for.

| Subject | Owner | Rule |
|---|---|---|
| What counts as proof · report format | `audit-app` | `CONTRACTS.md` |
| Runtime: concurrency, state, types, panics, test strength | `code-review` | *a test that has never failed proves nothing* |
| Contracts: IPC, API, layers, integrations | `code-review` | both sides crossed by test, not by reading |
| Performance budgets | `code-review` | **no measurement, no finding**; no budget, no rule |
| Maintainability: size, structure, duplication, named values, swallowed errors | `code-review` | *code another person can change without its author* — budgets with a ratchet, plus the M axes |
| Security: input, auth, tenants, paths, processes, dependencies | `security-audit` | OWASP ASVS 5.0 + the product's threat model |
| Persistence and recovery | `reliability-audit` | migration from **every** version ever published; crash at the worst moment |
| Diagnosability in production | `reliability-audit` §2 | *a customer says "doesn't work on version X" — what can you find out?* |
| Flows and UX heuristics | `design-pro` | NN/g + observed on the running app |
| Accessibility | `design-pro` | **WCAG 2.2 AA, with the criterion named** |
| i18n | `design-pro` | key parity enforced by the build |
| Design-system visual language and mechanics | `ui-system` | OKLCH tokens, `data-ui` contract — and **never closes an accessibility gate** |
| Distribution, supply chain, deploy, CI | `release-audit` | clean clone → one command → the same artifact |
| Sale, activation or checkout, first run, legal | `commercial-readiness` | the failing paths were walked, not just the happy one |
| Public web surface: SEO, GEO, CWV, cookies, CRO, links | `audit-website` | 7 pillars + deep SEO engine; consent prior to fire |
| Requirements: problem, acceptance criteria, out of scope | `spec` | a criterion names the observable proof it needs |
| New app: PRD, agent instructions, regression log | `prd` | only confirmed decisions; the rest is a pending decision with an owner |
| Diagnosis: reproduction, cause, regression | `diagnose` | *a bug is fixed when a test that failed on it passes* |
| Project vocabulary and decisions | `spec` | one term, one meaning; a decision recorded once, never edited |
| Planning: the way when it is not visible | `map` | plan, don't do — the route is clear when nothing is left to decide |
| Work breakdown | `slice` | a slice cuts every layer and is verifiable alone |
| Investigation | `research` | the source that owns the claim, with the version it holds for |
| Design questions | `prototype` | throwaway code that answers one question |
| Intake of external work | `triage` | one category, one state, and the claim verified before any brief |
| Release execution | `ship` | verified in production, and reversible before it starts |
| Human-only setup | `wizard` | if an agent can run it, it is not a wizard step |
| Structural debt | `improve` | no proof of no-change, no refactor |

Every owner declares `platforms:` in its `instruments.yaml` (web, desktop, both). A project's
`gates.json` declares `platform:`; checks tagged for the other platform
resolve `NOT_APPLICABLE/platform`. This is how one plugin serves a
Cloudflare Worker and a Tauri binary without inventing rules for either.

Some skills are not owners of a subject: `verify` and
`drive-app-window` are proof capabilities; `ship` executes what
`release-audit` and `verify` rule on;
`start-work`/`review-change`/`close-work` are the work cadence; `grill` is
the interview and `handoff` the package; and `bootstrap-project` is the
generator — **and the first thing to run**,
because it writes the four project adapters that make the generic
owners bite on a concrete codebase.

---

## 5. Closed decisions — don't reopen without new reason

Anyone evaluating saves time knowing what has been discussed and why.

| Decision | Reason |
|---|---|
| The install unit is the **plugin**; the activation unit is the **skill** | `description`s are always in context; bodies only load when they trigger |
| A **sub-topic** is a reference, not a skill | a reference doesn't pay permanent context |
| A skill that **asserts facts about a repository** lives in that repository's commit | the plugin is agnostic; what it knows about the project is the local adapter |
| **Multiple instruments** per rule | §3.2 — reducing loses coverage |
| The orchestrator **does not run commands** against the audited repo | running commands declared by the target is arbitrary execution driven by the target |
| **No numeric score** | gate ≠ score |
| Each `description` **≤ 250 characters** | every description is in context on every turn; the platform limit is 1024, and the host drops skills silently above its total budget |
| Two owners that touch **name each other** in the `description` | unilateral disambiguation lets the other win by accident; it's the pair that fails, not the file |
| **No change log, no decision records, no glossary file** — neither in the plugin nor asked of a project | each grows with every change and drifts from the code; the reason sits beside the rule (§3.5), the story is `git log` |
| **Not taken as owners:** `retro`, `teach`, `to-questionnaire`, `loop-me`, the writing-* family, host-specific setup skills, `tdd` as a skill, the five-bucket taxonomy, changesets with a release workflow, a docs page per skill | each duplicates an owner already here or pays permanent context for a verb nobody types |

A decision that **was** reopened, registered as such: the original
premise was *"a subject is not a skill"*. The plugin allows
subject-as-skill when the owner has its own verb and trigger, and
requires sub-topic-as-reference. The cost of that reopening is
measurable and declared — see §6.

---

## 6. What counts as being well made

Falsifiable criteria. The plugin refutes itself if it fails two.

| Criterion | How you verify it |
|---|---|
| Every `description` ≤ 250 chars | `python scripts/measure-descriptions.py skills` — exit 0 |
| Permanent context cost | same command over the plugin + the project's adapters; total declared in README |
| No PASS without a trace | `python skills/audit-app/scripts/validate_evidence.py --repo <repo>` — 0 `no-log` downgrades |
| Manifests coherent | `python -m pytest tests -q` — every owner has `platforms:`, every accepted producer exists |
| Bilateral pairs complete | every pair in `POLICY §1.2` is named by both sides (description or Boundaries) |
| Coherent authority chain | every external `producer` listed in the owner's `instruments.yaml` |
| Every subject owner has canonical checks | `CONTRACTS.md §7.4` against `POLICY.md §1` |
| Generator produces skills that pass the same audit | instantiate the templates in an empty repo and run the linter |
| No count stored in a document | a number lives in an evidence file with its `command` and `log`, or is not written |

Numbers are not repeated in this document because they change every
release. The commands above are the source of truth; run them.

---

## 7. Deliberately out of scope

- Does not correct anything. Audits, and the correction is another
  session with another request.
- Does not publish, does not bump versions, does not create tags.
  `release-audit` audits the pipeline; it does not run it.
- Does not do product analytics, growth, or usage metrics — usage is
  not quality.
- Does not give legal advice. Establishes facts verifiable in the repo
  and flags where a decision by whoever sells is needed.
- Does not replace human judgment on anything that requires seeing the
  app run; what it does is force declaring when it wasn't seen.

---

## 8. Where each thing lives

| File | Owns |
|---|---|
| `README.md` | how to install, first command, structure map |
| `PURPOSE.md` | this document — what the plugin is for |
| `CONTRACTS.md` | what counts as proof, and how proof travels (schema, channel, severity, gates) |
| `POLICY.md` | who owns what — subject authority, activation, local adapter, discovery |
| `skills/<name>/SKILL.md` | the verb, the trigger, and that owner's workflow |
| `skills/<name>/instruments.yaml` | which external `(producer, instrument)` that owner accepts |
| `adapter-contracts/<name>.md` | what a local adapter must provide |
| `scripts/measure-descriptions.py` | the single source of truth on `description` counts |

**What still remains.** One thing, and no file in the plugin can close
it: install the plugin, run `audit-app` against a real project, and
compare the verdict with a hand-made audit of the same commit. That is
the gate that separates "the plugin is coherent" from "the plugin is
right".

Extensions, not missing pieces:

- `audit-app` speaks two vocabularies: `CONTRACTS` (`PASS`/`FAIL`/
  `NOT_VERIFIED`) and its report format (`PROVEN`/`CLEARED`/`UNPROVEN`).
  The mapping is in `skills/audit-app/references/contract-and-evidence.md`;
  collapsing to one moves `validate_report.py` and its fixtures together.
- More instruments the runner can execute without a project harness:
  Lighthouse for `web.core-web-vitals`, `cargo deny` for
  `sec.deps-provenance`, a two-build hash compare for
  `release.reproducible-artifact`.
