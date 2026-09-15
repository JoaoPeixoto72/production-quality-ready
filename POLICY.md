# POLICY — plugin `production-quality-ready`

Plugin governance. **Authoritative** on: who owns which subject, when a
skill activates, how it composes with a local adapter, how conflicts
between owners are resolved.

Cross-references:

- What counts as evidence, gate machinery, schemas → `CONTRACTS.md`.
- What is proposed and why → `PLAN.md`.
- Purpose of the plugin, closed decisions, acceptance criteria →
  `PURPOSE.md`.

A discrepancy between this file and a skill is always the skill's
defect.

---

## 1. Authority per subject

Every subject has **exactly one** owner. The owner declares the rule
(named and versioned). Other skills may cite the rule; none rewrites
it.

Complete table in `PURPOSE.md §4`. This section rules the mechanics of
that table.

### 1.1 Sub-topics with their own reference

When a subject has meaningful sub-topics (e.g.
`commercial-readiness` covers activation, first run, legal), each
sub-topic lives in a **reference file inside the owner's folder**, not
as its own skill.

Reason: a reference doesn't pay permanent context; a skill does. A
sub-topic that becomes a skill either has its own verb and trigger
(and then it is a real owner, not a sub-topic) or it doesn't (and then
it lives as a reference).

The `commercial-readiness` owner ships `references/activation.md`,
`references/first-run.md`, `references/legal.md`. The `design-pro`
owner ships 21 domain references. Neither generates a permanent
context cost beyond its own `description`.

### 1.2 Bilateral delimitation

Whenever two owners touch the same subject (one as rule, another as
instrument, or two adjacent sub-topics), each `SKILL.md` **names the
other** in the `description`. Rule inherited from
`skill-auditor` POLICY §11.

Pairs that touch:

| Pair | How they delimit |
|---|---|
| `design-pro` ↔ `ui-system` | design-pro says "don't build the DS — that's ui-system"; ui-system says "UX/a11y audit not touching the DS — that's design-pro" |
| `design-pro` ↔ `audit-app` | design-pro says "full app audit — that's audit-app"; audit-app says "single-screen UX review — that's design-pro" |
| `code-review-runtime` ↔ `code-review-contract` | runtime says "contracts between parts — that's contract"; contract says "runtime behaviour — that's runtime" |
| `code-review-runtime` ↔ `verify` | runtime says "visual proof in the window — that's verify"; verify says "cargo test / automated tests — that's code-review-runtime" |
| `code-review-contract` ↔ `security-audit` | contract says "untrusted input — that's security"; security says "shape of the contract — that's contract" |
| `release-audit` ↔ `security-audit` | release says "signing, SBOM — that's release"; security says "vulnerable-dependency analysis — that's security" |
| `commercial-readiness` ↔ `design-pro` | commercial says "onboarding UX — that's design-pro"; design-pro says "activation, licence — that's commercial" |
| `observability` ↔ `reliability-audit` | observability says "data recovery — that's reliability"; reliability says "diagnose in production — that's observability" |
| `verify` (universal) ↔ `drive-app-window` | verify says "drive the Win32 window — that's drive-app-window"; drive-app-window says "proof strategy — that's verify" |
| `audit-app` ↔ `skill-auditor` | audit-app says "audit skills — that's skill-auditor"; skill-auditor says "audit the app — that's audit-app" |
| `audit-app` ↔ `review-change` | audit-app says "review a PR — that's review-change"; review-change says "full app audit — that's audit-app" |
| `start-work` ↔ `review-change` | start-work says "review written code — that's review-change"; review-change says "open a work session — that's start-work" |
| `review-change` ↔ `close-work` | review-change says "update documents at close — that's close-work"; close-work says "review code before — that's review-change (comes first)" |
| `start-work` ↔ `close-work` | start-work says "close and update documents — that's close-work"; close-work says "open a work session — that's start-work" |

The work-cycle pairs form a **triangle**, not a chain — a user can type
the wrong verb directly, not only the adjacent one. Every skill in the
cycle delimits against the other two.

The `skill-auditor` verifies each pair mechanically as a phase gate.

### 1.3 Who declares `PASS`/`FAIL`

**Only the rule's owner.** Other skills produce candidates (instruments,
`CONTRACTS §2.2`) and write them as evidence, but the final verdict of
a check is always the owner's.

**Mechanical verification** — validation of the
`producer → instrument → owner` chain is formalized in `CONTRACTS §4.5`.
Each owner declares the `(producer, instrument)` pairs it accepts in an
`instruments.yaml` at the skill root. An evidence file with `owner: X`,
`producer: Y ≠ X` is only accepted by `audit-app` when
`X/instruments.yaml` lists `Y` with the used `instrument:`. Missing
manifest or unlisted pair → `NOT_VERIFIED` with reason
`unauthorized-instrument`.

---

## 2. Activation

### 2.1 Founding rule

Each skill wakes **only when called**. Never by another skill.

Who can call a skill:

- the user, typing something in the prompt that triggers the
  `description`;
- the harness (IDE, CI), invoking explicitly;
- **never** another skill.

### 2.2 `audit-app` — orchestrator that doesn't invoke

`audit-app` doesn't invoke other skills. It:

1. Discovers applicable owners from the project's `.claude/gates.json`.
2. Reads evidence from `.audit/**/*.evidence.yaml`.
3. Validates each file against `CONTRACTS.md`.
4. Aggregates by owner, applies declarative gates.
5. Emits report.

If an owner's evidence is missing, the report reports
`Coverage: BLOCKED (n/m)` for that owner. **`audit-app` does not
activate the owner.** It announces what is missing; the human /
pipeline is who calls the owner to produce the evidence.

The alternative — an orchestrator that invokes eleven owners on its
own — collapses the composability the plugin was built to preserve.

Under strict read-only (`CONTRACTS §7.5`): `audit-app` doesn't run any
command against the audited repo. Not build, not tests, not scripts
declared in `gates.json`. The `adapter-hints:` section of the target's
`gates.json` is metadata for local adapters that emit their own
evidence; **the orchestrator never reads it**.

### 2.3 Optional order, same result

Within a project session, owners may be called in any order. Each
writes its evidence to `.audit/<owner>/`. `audit-app` reads what
exists. Two runs with different call orders on the same set of files
produce the same report.

Consequence: an owner can run alone. Nightly CI running only
`security-audit` doesn't drag anything else.

### 2.4 Skills that don't emit evidence

Some plugin skills don't emit evidence for `audit-app`. They serve
other purposes:

| Skill | Purpose |
|---|---|
| `skill-auditor` | Audits the skills themselves. Emits its own report format. Doesn't pass through `audit-app`. Mechanical isolation in `CONTRACTS §3.5`; editorial guidance in §2.4.1 below. |
| `drive-app-window` | Technical capability (Win32/WebView2). *Used* by other skills' instruments; doesn't emit evidence on its own. |
| `bootstrap-project` | Generator. Writes files in the user's repo. Not an auditor. |

### 2.4.1 Editorial guidance for the `skill-auditor` (non-mechanical)

`CONTRACTS §3.5` only knows how to mechanically reject
`producer: skill-auditor` outside `.audit/skill-auditor/`. Two
situations still require editorial judgment from the human auditor or
from `skill-auditor` itself as a concern (not a blocker):

- An owner emits a check whose `check:` semantically means "this skill
  is well written" (e.g. `owner: design-pro`,
  `check: description-well-formed`). That is `skill-auditor`'s subject,
  not `audit-app`'s. **Mark as `Concern` in `skill-auditor`'s report;
  refuse the skill merge.**
- A reference inside a skill audits the skill's own structure —
  suspicious duplication of responsibility. **Mark as `Concern`.**

None of these situations is blocked by `audit-app` at runtime.

---

## 3. Local adapter

Some skills of the plugin are **contract, not implementation** — the
universal `verify`, and the three of the work cycle
(`start-work`, `review-change`, `close-work`). The plugin carries the
rule; each project supplies the local adapter with its paths, commands,
and specific invariants.

### 3.1 Frontmatter

The universal skill carries `requires-adapter: true` and
`adapter-contract: adapter-contracts/<name>.md`. The local adapter
carries `extends: production-quality-ready::<name>@1.x`. Without an adapter,
the universal skill returns `NOT_VERIFIED/missing-adapter`
(`CONTRACTS §4.5`).

Contract for each adapter lives in `adapter-contracts/<name>.md` at
the plugin root — required frontmatter, required body sections, what
the adapter does not do.

### 3.2 Location of the adapter

Local adapter lives in `.claude/skills/<name>/` inside the target repo.
It travels with the project's commits. Its version is independent of
the plugin's; it declares which `extends` it inherits from.

Two options for the `contract:` path (`bootstrap-project` step 5b):

- **Plugin installed globally** → absolute path to
  `production-quality-ready/CONTRACTS.md`. No duplication.
- **Local snapshot** → `bootstrap-project` copies `CONTRACTS.md` to
  `<repo>/.claude/CONTRACTS.md.snapshot`; the adapter uses
  `../CONTRACTS.md.snapshot`. The snapshot carries a header saying
  which version it is a copy of; editing the snapshot is not editing
  the contract.

### 3.3 Division of responsibility

Universal skill owns:

- The rule (the ordered steps, the rules that never change).
- Cross-references to plugin owners.
- The list of what the adapter must supply.

Local adapter owns:

- Paths of concrete files (`ESTADO.md`, project artifacts).
- Commands to build / test / launch the app.
- The list of invariants **this project has already paid for once**,
  each with the example that motivated it.
- Traps specific to this project not covered by the plugin.

The local adapter cannot rewrite the rule of the universal, cannot
duplicate the rules of other owners, and cannot assert facts about
other projects.

---

## 4. Bilateral delimitation (mechanical)

Rule written in POLICY §1.2 and verified by `skill-auditor` as a phase
gate.

**Rule 4.1.** For each pair `(A, B)` in the §1.2 table, `A`'s
`description` mentions `B` and `B`'s mentions `A`. Missing on either
side = the *pair* fails, not the file.

**Rule 4.2.** The `skill-auditor` verifies mechanically:

1. Enumerates pairs from the §1.2 table (declarative source,
   editable).
2. For each side, checks that the token of the other owner appears in
   the `description`.

**Rule 4.3.** Adding a subject that touches an existing one (or
splitting an existing owner) adds a row to the table and requires a
bilateral refactor in the same release as the change.

---

## 5. Discovery by the orchestrator

`audit-app` needs to know which owners are applicable to the project.
In order:

### 5.1 Project gate pack

Default source: `<repo-root>/.claude/gates.json`. Structure:

```json
{
  "plugin": "production-quality-ready",
  "plugin-version": "^1.0.0",
  "owners": {
    "code-review-runtime": {
      "applicable": true,
      "adapter-hints": {
        "build-command": "cargo build --release",
        "test-command": "cargo test"
      }
    },
    "code-review-contract": { "applicable": true },
    "security-audit": { "applicable": true },
    "seo-audit": {
      "applicable": false,
      "not-applicable": "no indexable web surface"
    },
    "…": "…"
  },
  "gates": {
    "release-candidate": { "owners": ["code-review-runtime", "security-audit"] },
    "sellable": { "owners": ["*"] }
  }
}
```

**Rule 5.1.1 (declared scope).** Every plugin owner is listed. An
inapplicable owner declares `not-applicable: "<reason>"`. Omitting an
owner is a defect of the file: `audit-app` aborts with
`owner-undeclared: <slug>`.

Reason: "silent omission" is silent PASS. Rule inherited from
`auditar-app`.

**Rule 5.1.2 (`adapter-hints:`).** The `adapter-hints:` section is
**metadata for local adapters that emit their own evidence** (e.g. a
local `code-review-runtime` adapter that knows `cargo build`).
`audit-app` **never reads it**. Not runnable commands from
`audit-app`'s point of view.

**Rule 5.1.3 (renaming from v1.2.x).** The previous name of this
section was `preconditions:`. From v1.3.0, it's `adapter-hints:`. The
old name suggested runnability by the orchestrator, which never
happened; the new name says exactly what it is (a hint for the
adapter).

**Rule 5.1.4 (do not read).** Explicit for verbatim reading of this
POLICY: **the orchestrator does not read `adapter-hints:`.**
Emphasized here to prevent a future refactor from confusing the fields.

### 5.2 Project-type detection

If no `.claude/gates.json`, `audit-app` tries detection by manifest
files (`Cargo.toml` → runtime/contract Rust profile; `package.json` +
Web framework → runtime frontend + seo-audit; …).

Detection is a **starting suggestion**, not authority. First run
proposes a gate pack; the user confirms and commits.

### 5.3 Explicit activation

Without detection or gate pack, the user passes `--owners X,Y,Z`
explicitly. `audit-app` runs only over those and declares the reduced
scope in the report.

---

## 6. Versioning

### 6.1 Semver per skill

Each skill has an independent version in its `SKILL.md` frontmatter.
Breaking changes bump major.

### 6.2 Plugin version

The plugin has an aggregate version, updated when there is a coherent
release of the whole. Follows the majority-of-changes semver: a major
inside a skill can be a minor of the plugin if the rest doesn't
break.

The plugin's contract (`CONTRACTS.md`) has its own version, quoted at
the top of that file. `evidence-schema` in each skill's frontmatter
tracks the major of the contract.

### 6.3 Migration between majors

When a skill's or the contract's major changes, the plugin ships a
migration script or migration note. Legacy files remain readable in
`NOT_VERIFIED` mode with reason `stale-schema`.

Ex: `evidence-schema: 1.2.x` → `1.3.x` — files
in `1.1.x` become `NOT_VERIFIED` until re-emitted. Documented in the
skill's migration.

### 6.4 Project files across majors

The `.claude/gates.json` of a project follows the plugin's major.
Bumping the plugin locally requires updating the file too. The
`bootstrap-project` skill has a `--migrate <from-version>` mode
(planned) to help.

---

## 7. Non-goals

- **Correcting the app.** Audits and announces; correction is another
  session with another request.
- **Executing pipelines.** Reads pipeline state (SBOM, signature); does
  not run publishing.
- **Product decisions.** Says whether legal clauses exist, not whether
  they are the right business call.
- **Replacing human judgment.** Where a check requires seeing the app
  run and the harness cannot, the owner reports `NOT_VERIFIED` with
  `needs-human`. It doesn't guess.

---

## Appendix A — changes since v1.0.0

- **v1.5.0** — POLICY translated into English (whole plugin now in
  English); §1.2 recount cross-checked with the pair-check script.
  No breaking change; `evidence-schema: 1.3.x` unchanged.
- **v1.4.0** — §1.2 grows with the pairs the pair-check found after
  the audit-owner bodies were written: `code-review-runtime ↔ verify`,
  `audit-app ↔ review-change`, and the three of the work-cycle
  triangle (`start-work ↔ review-change`,
  `review-change ↔ close-work`, `start-work ↔ close-work`). The
  editorial adds a paragraph explaining why the work cycle is a
  triangle, not a chain: a user can type the wrong verb directly, not
  just the adjacent one.
- **v1.3.0** — sync with `CONTRACTS.md v1.3.0`. §5.1: the
  `preconditions:` block of `gates.json` is renamed `adapter-hints:`;
  new rule 5.1.4 makes explicit that the orchestrator **does not
  read** that section. Alignment with the founding rule "audit-app
  doesn't invoke". Compatible with `evidence-schema: 1.3.x`.
- **v1.2.0** — bilateral delimitation as phase gate. §5.1 corrected
  from silent PASS ("simply doesn't count") to explicit non-applicability
  with reason. Inherits the "requested scope, not possible scope"
  principle from `auditar-app`. §2.4.1 new — editorial guidance for
  `skill-auditor` absorbing the semantic part `CONTRACTS §3.5` stopped
  trying to verify mechanically.
- **v1.1.0** — §1.3 now cites the mechanical mechanism
  (`instruments.yaml` + `CONTRACTS.md §4.5`) instead of the
  unverifiable promise of v1.0.0.
- **v1.0.0** — first version. Establishes the subject-authority table,
  local-adapter pattern, bilateral delimitation with mechanical
  pair-check, discovery by gate pack + detection + explicit activation,
  versioning rules, and non-goals. Compatible with
  `evidence-schema: 1.x`.
