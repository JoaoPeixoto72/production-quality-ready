# PURPOSE — what `production-quality-ready` is for

Orientation document. Read **before** evaluating the plugin. Answers one
question: *what does this exist for, and what counts as being well
made.*

Doesn't tell the story of how it was designed. Anyone needing the reason
for a specific choice goes to `PLAN.md`; the rules live in
`CONTRACTS.md` and `POLICY.md`.

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

## 3. The four ideas holding it up

Everything else is a consequence of these. Anyone evaluating the plugin
is, at bottom, checking whether they hold in what is written.

### 3.1 One subject, one owner, one rule

Every subject has **exactly one** owner, and that owner declares the
**rule** — the criterion that decides `PASS`/`FAIL`, named and
versioned. Other owners may *cite* the rule; none rewrites it.

The historical defect this corrects: contrast had three owners with
three criteria — WCAG 4.5:1, an OKLCH ΔL heuristic, and a gate that
decided sellability with no number at all. Three answers to the same
question is not robustness; it is having no answer.

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

Every owner declares `platforms:` (web, desktop, both). A project's
`gates.json` declares `platform:`; checks tagged for the other platform
resolve `NOT_APPLICABLE/platform`. This is how one plugin serves a
Cloudflare Worker and a Tauri binary without inventing rules for either.

Some skills are not owners of a subject: `verify` and
`drive-app-window` are proof capabilities;
`start-work`/`review-change`/`close-work` are the work cadence; and
`bootstrap-project` is the generator — **and the first thing to run**,
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
| Manifests coherent | `python skills/audit-app/scripts/test_validate_evidence.py` — every owner has `platforms:`, every accepted producer exists |
| Bilateral pairs complete | every pair in `POLICY §1.2` is named by both sides (description or Boundaries) |
| Coherent authority chain | every external `producer` listed in the owner's `instruments.yaml` |
| Every subject owner has canonical checks | `CONTRACTS.md §7.4` against `POLICY.md §1` |
| Generator produces skills that pass the same audit | instantiate the templates in an empty repo and run the linter |
| No number asserted without a command or an owning file | every count in the docs must be reproducible |

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
| `PLAN.md` | what was proposed, the order, and each correction with its reason |
| `skills/<name>/SKILL.md` | the verb, the trigger, and that owner's workflow |
| `skills/<name>/instruments.yaml` | which external `(producer, instrument)` that owner accepts |
| `adapter-contracts/<name>.md` | what a local adapter must provide |
| `scripts/measure-descriptions.py` | the single source of truth on `description` counts |

**What still remains.** One thing, and no file in the plugin can close
it: install the plugin, run `audit-app` against a real project, and
compare the verdict with a hand-made audit of the same commit. That is
the gate that separates "the plugin is coherent" from "the plugin is
right".
