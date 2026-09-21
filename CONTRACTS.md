# CONTRACTS — plugin `production-quality-ready`

Plugin mechanical contract. **Authoritative.** Every plugin skill refers
to this file by its root (`contract: CONTRACTS.md`); the
`skill-readiness-auditor` resolves the path from the plugin root. A discrepancy
between this file and a skill is always the skill's defect.

**Contract version**: 1.4.0

This file **does not describe workflows** — it describes *what counts
as proof* and *how skills speak to each other*. Authority, activation
and local-adapter rules live in `POLICY.md`.

---

## 1. Vocabulary

Seven units. One sentence each. No eighth.

| Unit | Definition |
|---|---|
| **Skill** | Activation unit. Pays context whenever the plugin is installed. Has `SKILL.md`, `description`, and a verb with its own trigger. |
| **Subject** | Responsibility unit. Every subject has exactly one owner. A subject does not pay context: it lives inside a skill or is documented as a sub-topic in a reference. |
| **Reference** | Knowledge unit. Pays context only when its owning skill loads it. Has a declared owner in the header. |
| **Instrument** | Detection unit. Produces *candidates*, never findings. A subject has N independent instruments; none closes a verdict on its own. |
| **Evidence** | What an instrument returned, linked to `path:line` or an observable artifact. Without evidence, no finding. |
| **Verdict** | The result the rule produces on a check given the evidence. One of: `PASS`, `FAIL`, `NOT_VERIFIED`, `NOT_APPLICABLE`. |
| **Gate** | Declarative condition over a set of verdicts that opens or blocks a phase (`Production Ready`, `Release Candidate`, …). A gate has no score; it is binary. |

**Not vocabulary of the contract** — and therefore absent from every
schema below: `finding` (it's a `FAIL` verdict plus evidence), `score`
(deliberately absent; see §7), `warning` (maps to `severity`),
`suggestion` (maps to `severity: INFO`).

---

## 2. Rule vs instrument

Distinction that fixes the historical contrast defect (three owners,
three rules, none cited by name).

| Role | What it does | Closes the verdict? |
|---|---|---|
| **Rule** | The standard or criterion that decides `PASS`/`FAIL`. Named, versioned, external where one exists. | **Yes** |
| **Instrument** | Independent detector that produces *candidates*. A skill may declare N instruments per rule. | **No** |
| **Evidence** | What an instrument produced, with `path:line` or artifact. Without it, the verdict is `NOT_VERIFIED`. | Never alone |

**Rule 2.1.** A rule belongs to **one** owner. Multiple owners can
*cite* the same rule; none *rewrites* it.

**Rule 2.2.** An instrument never declares `PASS`/`FAIL` — it declares
`candidate`, `clear`, or `unproven`. Conversion into a verdict belongs
to the rule's owner.

**Rule 2.3.** An instrument may belong to a skill different from the
rule's owner. Canonical example:

```
Subject:     text contrast
Owner:       design-pro
Rule:        WCAG 2.2 SC 1.4.3 (4.5:1 normal text, 3:1 large text)
Instruments:
  - ui-system::audit_ui.py         # OKLCH ΔL over tokens.css — static candidate
  - design-pro::screenshot-sample  # sample of rendered pixels — perceptual candidate
  - design-pro::keyboard-traversal # candidate for visible focus (for SC 2.4.7)
```

`ui-system` owns the **instrument** `audit_ui.py` (design system
mechanics), not the contrast rule. `design-pro` owns the WCAG **rule**.
Both are written that way in the skill header.

---

## 3. Evidence schema

Every output a skill produces for the orchestrator has this shape. A
skill emits one evidence unit per *check*, in one file per check
(§4).

### 3.1 Required fields

```yaml
check:            keyboard-focus-visibility        # string, kebab-case, unique per owner
owner:            design-pro                       # slug of the skill owning the RULE
producer:         ui-system                        # slug of the skill that WROTE this file
instrument:       audit_ui.py                      # id of the instrument inside the producer
rule:             WCAG 2.2 SC 2.4.7                # human-readable rule name
rule-version:     wcag-2.2-AA                      # see §3.3
evidence-schema:  1.1.0                            # see §6
methods:                                           # instruments used; at least one
  - dom-inspection
  - screenshot
  - keyboard-traversal
evidence:                                          # see §3.4
  - path: src/ui/Dialog.tsx:42
    excerpt: "outline: none;"
    kind: source
result:           FAIL                             # one of: PASS | FAIL | NOT_VERIFIED | NOT_APPLICABLE
severity:         HIGH                             # required if result=FAIL; see §5
confidence:       OBSERVED                         # one of: OBSERVED | INFERRED | UNKNOWN
```

**Rule 3.1.1 (authority).** `owner` is the skill that owns the rule —
who decides the verdict. `producer` is the skill that produced this
file — who operated the instrument. Both are required and may be
different. `instrument` identifies *which* instrument of the
`producer` was used, so authority validation (§4.5) is mechanically
resolvable.

When `owner == producer`, that's a signal that the owner ran one of its
own instruments — common and legitimate. What is **not** accepted is
`owner ≠ producer` without `instrument` declared as belonging to
`producer` in the instrument manifest that `owner` recognises (§4.5).

**Rule 3.1.2 (forbidden defaults).** A 1.2 parser that finds `producer:`
missing reads the field as `producer: unknown` — and `unknown` **never**
satisfies step 3 of §4.5, nor is it accepted by any instruments
manifest. The file reads as `NOT_VERIFIED` with reason
`missing-producer`. A compatibility default may degrade; it may not
promote. The v1.1.0 had a promoting default (`producer := owner`) that
fabricated authority — removed in 1.2.0.

**Rule 3.1.3.** Missing `owner:` is always `NOT_VERIFIED` with reason
`missing-owner`, without default. `owner` is the root of the authority
chain and has no reasonable value to assume.

**Rule 3.1.4.** Missing `instrument:` with `producer` present is
`NOT_VERIFIED` with reason `missing-instrument` — the §4.5 manifest
requires a `(producer, instrument)` pair, not a bare producer.

### 3.2 Optional fields

```yaml
title:      "Focus outline removed on Dialog"      # readable; if omitted, derived from check
impact:     "Keyboard users cannot see focus."     # readable; required if severity ≥ HIGH
fix:        "Restore outline; use outline-offset." # readable; suggested fix
root-cause: RC-focus-outline-suppressed            # see §4.4; optional, required if you want dedup
context:                                           # free metadata for the orchestrator
  scope: src/ui/**
  captured-at: 2026-09-14T00:00:00Z
  captured-by-version: ui-system@1.0.0             # semver of the PRODUCER
```

**Rule 3.2.1.** No field beyond those declared in 3.1/3.2 is read by
the orchestrator. Unknown fields are preserved in the report but do
not affect verdicts.

### 3.3 `rule-version`

Semver or external standard identifier. Required for owners with an
external standard; optional for owners with their own rule.

| Owner | `rule-version` required? | Expected format |
|---|---|---|
| `design-pro` | yes | `wcag-2.2-AA`, `wcag-2.2-AAA`, `hig-2026`, `material-3` |
| `seo-audit` | yes | `sarif-2.1.0`, `schema-org-2025-10` |
| `security-audit` | yes | `owasp-asvs-5.0`, `nist-ssdf-1.1` |
| `code-review-runtime` | optional | semver of the project's gate pack |
| `code-review-contract` | optional | idem |
| `reliability-audit` | optional | idem |
| `performance-audit` | optional | idem |
| `observability` | optional | idem |
| `release-audit` | optional | idem |
| `commercial-readiness` | optional | idem |
| `ui-system` | no | internal contract is `evidence-schema` |

**Rule 3.3.1.** Missing where required → the orchestrator reads the
check as `NOT_VERIFIED` with reason `missing-rule-version`,
regardless of the `result:` the skill wrote.

### 3.4 Evidence items

Each item in `evidence:` is an object:

```yaml
- path:    <string>            # required; path:line, or URL, or artifact
  excerpt: <string>            # required for kind=source; optional otherwise
  kind:    source              # one of: source | screenshot | log | measurement | command-output | external
  hash:    <sha256>            # required for kind ∈ {screenshot, measurement, log}
```

**Rule 3.4.1.** `result: FAIL` without `evidence:` (0 items) → the
orchestrator discards the check as `NOT_VERIFIED` with reason
`missing-evidence`.

**Rule 3.4.2.** `result: PASS` without `evidence:` is accepted; the
rule closes by *absence of the problematic condition*. `confidence:`
reflects how the absence is known (`OBSERVED` if you looked;
`INFERRED` if deduced; `UNKNOWN` is forbidden on `PASS`).

### 3.5 Mechanical isolation of the skill meta-auditors

Mechanical rule, verifiable by `audit-app` without semantic
interpretation:

**Rule 3.5.1.** A file at `.audit/<owner>/*.evidence.yaml` with
`producer: skill-readiness-auditor`, `producer: skill-security-auditor`,
or `producer: skill-release-gate` is only accepted if `<owner>` is
that same skill. In any other directory, the file is rejected with
reason `skill-meta-auditor-out-of-scope`. The meta-auditors are not
instruments of any product owner.

**Rule 3.5.2.** A file at `.audit/skill-readiness-auditor/*.evidence.yaml`,
`.audit/skill-security-auditor/*.evidence.yaml`, or
`.audit/skill-release-gate/*.evidence.yaml` is ignored by `audit-app` —
the meta-auditors run in a separate plane and their output does not
enter any product gate.

**Note.** The semantic distinction "this skill audits itself as a
skill, rather than as a subject it owns" is not mechanically
verifiable and moved to `POLICY.md` as editorial guidance for the
skill meta-auditors. `CONTRACTS.md` defines only what the parser can
reject without interpretation.

---

## 4. Collection channel

Evidence **is a file, not a call**. No skill invokes another.

### 4.1 Canonical path

```
<repo-root>/.audit/<owner>/<producer>--<check-id>.evidence.yaml
```

- `<repo-root>` is the root of the audited repository.
- `<owner>` is the slug of the rule's owner (§3.1.1).
- `<producer>` is the slug of the skill that produced the file
  (§3.1.1). It appears in the name so that two producers of the same
  check for the same owner don't collide on disk.
- `<check-id>` is the file's `check:` value.

**Rule 4.1.1.** `.audit/` is always gitignored in the audited repo.
The plugin doesn't commit evidence.

**Rule 4.1.2.** A second file for the same
`<owner>/<producer>/<check-id>` triple during the same session
**replaces** the first; between sessions, `captured-at:` decides.

**Rule 4.1.3.** Two different producers emitting the same
`<owner>/<check>` don't replace each other — they coexist. Dedup
between them is a §4.4 matter, not a path matter.

### 4.2 Orchestrator idempotence

Running `audit-app` twice without executing any other skill produces
the same verdict. `audit-app`:

1. reads recursively `.audit/**/*.evidence.yaml`;
2. validates each file against this contract;
3. aggregates verdicts by owner;
4. applies gates (§7);
5. writes the report.

None of these steps writes to `.audit/`. None invokes another skill.
The order in which evidence arrived is irrelevant to the verdict; it's
only recorded in the report for debugging.

### 4.3 Declared coverage

**Absence ≠ PASS.** If `.audit/<owner>/` doesn't exist or is empty,
`audit-app` reports that owner as `Coverage: BLOCKED (0/N)` in the
report and assigns it no verdict. Inherits the `PROVEN` vs
`UNPROVEN` distinction from auditar-app, but attached to the owner
rather than the check.

**Rule 4.3.1 (mandatory fraction).** The report always writes
`BLOCKED (n/m)`, `PARTIAL (n/m)` or `COMPLETE (m/m)` — never the token
alone — where:

- **`m`** = number of canonical checks declared in §7.4 for the owner.
- **`n`** = number of those checks resolved to `PASS`, `FAIL` or
  `NOT_APPLICABLE`. `NOT_VERIFIED` doesn't count.

**Rule 4.3.3 (canonical checks are a pre-req).** An owner without an
entry in the canonical registry §7.4 has no `m`; reports
`BLOCKED (—/?)` with reason `no-canonical-registry`. There is no
"use what was emitted" fallback — that mechanism (v1.2.0) allowed an
owner to emit 3 of 20 possible checks and get `COMPLETE (3/3)`.
Registering canonicals is a precondition for the owner to close any
`coverage-complete` gate.

**Rule 4.3.2.** `BLOCKED (0/8)` and `BLOCKED (7/8)` are the same token
but **not the same knowledge state**. Without the fraction the reader
can't tell "hasn't looked" from "one left to close". The original
`auditar-app` paid this lesson once; the plugin inherits it from birth.

### 4.4 Dedup by root cause

Dedup is **deterministic and opt-in** — never heuristic. It only
merges what has been explicitly marked as the same cause.

**Rule 4.4.1.** Two checks are deduplicated **if and only if** both
declare the same value in the optional `root-cause:` field (§3.2). No
other combination (same line, same excerpt, same defect type)
triggers dedup.

**Rule 4.4.2.** `root-cause:` is optional. A check without
`root-cause:` is never deduplicated with another — even if both point
at the same line. The report shows both findings, each with its
`producer` and its `owner`.

**Rule 4.4.3.** The `root-cause:` identifier is kebab-case, starts
with a prefix declared by the emitting owner (`RC-`, or `<owner>::`
like `design-pro::focus-outline-suppressed`) — to reduce accidental
collision between owners that chose the same name for different
causes. The skill meta-auditors warn when two owners share a
`root-cause:` without distinct prefix.

**Rule 4.4.4.** Dedup by `root-cause:` produces a single aggregated
entry in the report, listing every distinct `producer` and `owner`
that contributed, all evidence concatenated, and the highest
`severity:` of the merged. The gate counts once.

**Note on design.** The temptation was to dedup by heuristic — "same
line, same type" — to save noise. Rejected because two distinct
problems on the same line by different owners are a real and common
case (an `<input>` without label is a11y **and** microcopy **and**
token violation). Implicit dedup hides findings; explicit dedup
forces the owner to own the merge.

### 4.5 Mechanical authority

The orchestrator validates each evidence file's authority with this
chain, in order:

1. **`owner`** exists and is a declared plugin skill.
2. **`producer`** exists and is a declared plugin skill.
3. If `owner == producer`: accepted. The owner ran its own instrument.
4. If `owner != producer`: the file is only accepted when the `owner`
   has declared the `(producer, instrument)` pair in its **external
   instruments manifest** (`instruments.yaml` at the skill root).
   Format:

   ```yaml
   # design-pro/instruments.yaml
   accepts:
     - producer: ui-system
       instrument: audit_ui.py
       for-checks: ["*-contrast", "*-focus-outline"]
     - producer: design-pro
       instrument: screenshot-sample
       for-checks: ["*"]
   ```

5. Missing manifest, or unlisted pair → the orchestrator reads it as
   `NOT_VERIFIED` with reason `unauthorized-instrument`.

**Rule 4.5.1.** A `producer` may write evidence for several `owner`s
if each of them declares the pair in its manifest. That is the
`producer → instrument → owner` chain `POLICY §1.3` demands and that
v1.0.0 had no way to validate.

**Rule 4.5.2.** The `skill-readiness-auditor` rejects a skill that declares
instruments without a manifest, and rejects a manifest pointing at
non-existent producers.

---

## 5. Severity taxonomy

Six levels. Each owner decides *when* it assigns — the internal logic
is not shared. Only the output language is common.

| Level | Common-language meaning |
|---|---|
| `BLOCKER` | Prevents normal operation or illegally sells the product. Closes the `Production Ready` gate. |
| `CRITICAL` | A real user loses data, is materially misled, or the product violates a cited standard. |
| `HIGH` | Serious friction; the product works but with visible defect for most users. |
| `MEDIUM` | Material defect in a normal case, workaroundable. |
| `LOW` | Defect in a limit case; trivially workaroundable. |
| `INFO` | Observation without defect; never closes a gate. Corresponds to `suggestion`. |

**Rule 5.1.** An owner cannot emit `BLOCKER` on a subject that isn't
theirs. If an external instrument (§2.3) produces a candidate with
severity that would warrant `BLOCKER`, the rule's owner decides
whether to promote it.

**Rule 5.2.** `result: PASS` with `severity:` present is forbidden.
`severity:` only exists for `FAIL` (required) and for `NOT_VERIFIED`
(optional, to signal that had it been known it was severe).

---

## 6. Compatibility

### 6.1 `evidence-schema`

Semver of this file's contract. Blocks aggregation **across majors**.

- **Major (X.0.0)** — parser-breaking change: new required field,
  rename, semantics swap. `audit-app` on major `X` **refuses** to read
  evidence with major `Y ≠ X` and emits `NOT_VERIFIED` for the owner
  with reason `schema-major-mismatch`.
- **Minor (1.X.0)** — new optional field, or new allowed instrument.
  Compatible with previous evidence.
- **Patch (1.0.X)** — text clarification, editorial fix. Zero semantic
  change.

### 6.2 `rule-version`

Semver or external standard identifier. **Does not block**
aggregation. The orchestrator records divergences (two checks on the
same subject with different `rule-version:`) but both count for the
owner's verdict.

**Rule 6.2.1.** An owner that bumps `rule-version` major (SC 1.4.3 →
SC 1.4.6, i.e. AA → AAA) declares it in the skill's `description`.
An audit requesting the AA rule still receives AA if the old evidence
hasn't expired.

### 6.3 Plugin version

`production-quality-ready` has its own semver. A plugin release pins one
`evidence-schema` version and one minimum-`rule-version` matrix per
owner. Individual skills keep their own semver and declare
compatibility with a range of plugin versions.

---

## 7. Gates

A gate is a binary condition over a set of verdicts. **There is no
score.** "94/100" does not open a gate; an open `BLOCKER` closes one.

### 7.1 Declarative syntax

A gate written in `POLICY.md` (or in a project gate pack) has this
form:

```yaml
gate:      production-ready
requires:
  - no-open: [BLOCKER, CRITICAL]
  - all-pass-in-owner: [security-audit, release-audit]
  - coverage-complete: [design-pro, code-review-contract]
  - conditional:
      when: project.sells == true
      require:
        - all-pass-in-owner: [commercial-readiness]
```

Predicates supported in v1.0.0:

| Predicate | Semantics |
|---|---|
| `no-open` | No `FAIL` with `severity:` in the list. |
| `all-pass-in-owner` | Every check emitted by those owners has `result: PASS`. |
| `coverage-complete` | **Every** canonical check of the owner (§7.4) resolved to `PASS`, `FAIL` or `NOT_APPLICABLE`; no `NOT_VERIFIED`. An owner without canonicals registered in §7.4 **cannot close** `coverage-complete` — reports `BLOCKED (—/?)` with reason `no-canonical-registry`. Registration in §7.4 is a precondition for closing a gate for that owner. |
| `conditional` | Sub-requirements evaluated only when the condition holds. Condition evaluated against the project's gate pack. |

### 7.2 Gate ≠ score

A gate does not expose percentage, grade or bar. A report may publish
coverage metrics *separately* (number of checks, severity
distribution) but those metrics never open or close a gate.

**Rule 7.2.1.** A skill that introduces a numeric score as output
violates this contract. The `skill-readiness-auditor` refuses.

### 7.3 Standard gates

The plugin defines three canonical gates in `POLICY.md`. A project
gate pack can add more but cannot remove these. **Every gate is
expressible with the four §7.1 predicates** — the prose below is not
a new predicate, it's the human reading of the declarative form.

| Gate | Declarative form | Human reading |
|---|---|---|
| `release-candidate` | `no-open: [BLOCKER]` + `coverage-complete: [code-review-runtime, verify]` | Compiles, tests ran, no BLOCKER. A LOW FAIL on a non-critical check does not stop a candidate. |
| `production-ready` | `no-open: [BLOCKER, CRITICAL]` + `coverage-complete: [<all-applicable-owners>]` + `all-pass-in-owner: [security-audit, release-audit]` | Every owner with complete coverage, no BLOCKER/CRITICAL, and the areas with non-negotiable integrity (security, release) 100 % PASS. |
| `sellable` | `production-ready` **and** `all-pass-in-owner: [commercial-readiness]` | Production-ready and fit to sell. |

**Rule 7.3.1 (severity ladder).** Gates are ordered by increasing
severity. `all-pass-in-owner` only enters where the domain integrity
is binary (a `LOW` security vulnerability is still a vulnerability;
an unsigned artifact is still unsigned). For continuous quality, the
right predicate is `coverage-complete` + `no-open` of the severity
that matters. The v1.1.0 had this inverted: a `FAIL LOW` in
`code-review-runtime` blocked `release-candidate` but not
`production-ready`. Fixed in 1.2.0.

### 7.4 Canonical checks a skill must emit

A `all-pass-in-owner` gate is only useful if it's known *which*
checks the owner commits to emit. This is the minimum registry — each
owner must emit every check listed here; a missing check reports as
`NOT_VERIFIED` and the gate doesn't close.

| Owner | Canonical check-id | Semantics |
|---|---|---|
| `code-review-runtime` | `build-passes` | The project compiles in a clean clone with the declared command. Owner emits the evidence; `audit-app` doesn't run the build (§7.5). |
| `code-review-runtime` | `tests-pass` | The declared test suite ends without failures. |
| `code-review-runtime` | `types-check` | The project's typecheck ends without error. |
| `code-review-runtime` | `test-strength` | Tests protect what they say they protect — a reversible minimal mutation turns the test red. "A test that has never failed proves nothing." |
| `code-review-runtime` | `risk-proof-matrix` | Every declared material risk has a named test or a `NO_PROOF` reason. |
| `code-review-runtime` | `tests-that-never-run` | No test outside discovery, filtered or `ignored` without recorded reason. |
| `code-review-contract` | `contracts-cross` | Contracts between parts (IPC/API) cross without inconsistency. |
| `verify` | `smoke-test-passes` | A manual/automated smoke test of the real app passes. |
| `security-audit` | `dependency-scan` | No dependency with a known `CRITICAL`+ vulnerability. |
| `security-audit` | `sast-run` | Static analysis ran and emitted no `CRITICAL`+. |
| `release-audit` | `reproducible-artifact` | Two builds of the same commit produce the same artifact. |
| `release-audit` | `signed-artifact` | Final artifact signed with a declared key. |
| `commercial-readiness` | `sell-01-activation` through `sell-06-end-of-payment` | Six SELL-* gates, each with its own check-id. |
| `design-pro` | `a11y-critical-flows` | Critical flows verified against WCAG 2.2 AA in an `INTERACTIVE` environment. |
| `observability` | `error-diagnosable` | An anonymous user error is diagnosable with what has been logged. |
| `reliability-audit` | `atomic-write` | No write path loses data on interruption. |
| `reliability-audit` | `migration-chain` | Migration from the earliest published version ends intact. |
| `performance-audit` | `budgets-declared` | Performance budgets exist in the project. |
| `performance-audit` | `budgets-met` | Each budget is measured in release and passes. |
| `ui-system` | `ds-boundary` | Application does not import internal DS directly. |
| `seo-audit` | `technical-seo-clean` | Technical SEO audit closes without critical `FAIL`. |
| `audit-website` | `website-readiness-clean` | 360º website audit closes without BLOCKER or CRITICAL failures. |

**Rule 7.4.1.** An owner may emit more checks than the canonicals;
never fewer. The `skill-readiness-auditor` verifies this list mechanically
against each skill's manifest.

**Rule 7.4.2.** A canonical check-id in this registry is reserved —
another skill cannot use the same `<owner>::<check-id>`.

### 7.5 `audit-app` does not execute commands

**Rule 7.5.1 (strict read-only).** `audit-app` does not run any
command against the audited repository. It doesn't read
`gates.json.preconditions`, doesn't invoke build systems, doesn't
execute scripts declared by the target. Its only disk operation is
reading `.audit/**/*.evidence.yaml` and writing the report.

**Rule 7.5.2 (build/tests/types are evidence like any other).** What
v1.2.0 called "preconditions" — that the tree compiles, that tests
pass, that typecheck closes — are now canonical checks of
`code-review-runtime` (§7.4). The owner that already owns the runtime
is the one that produces the evidence file with the result; a YAML
may disagree with the exit code that generated it, but that is a
known pain of the owner that decided to emit the evidence, not of the
orchestrator.

**Rule 7.5.3.** `POLICY §5.1` still allows a `build-command:` section
and similar in the project's `gates.json` — but only as **declarative
metadata** for use by the very owner that emits the evidence (e.g. a
`code-review-runtime` adapter that knows how to run `cargo build`).
None of those strings reaches `audit-app`.

**Design.** v1.2.0 tried to save ceremony ("a YAML to say cargo test
returned 0 is redundant") but the price was executing commands
declared by a file in the target repo — arbitrary execution driven by
the target. The original `auditar-app` has whole read-only doctrine
("Read-only. An audit observes; does not fix.") that this shortcut
violated. The right choice is the same one already made for every
other piece of evidence: what the orchestrator sees is a file. If an
owner wants its `build-passes` check to reflect the build exit code,
it's the owner that runs the command and emits the YAML — inside its
own harness, not audit-app's.

This rule closes defect C3 of PLAN §11.

---

## 8. Non-goals of this contract

What this file deliberately **does not** define, and lives in
`POLICY.md` or elsewhere:

- **Who** may declare `PASS`/`FAIL` on each subject (authority) —
  `POLICY.md` §1.
- **How** a skill wakes and who activates it — `POLICY.md` §2.
- **How** a local adapter declares itself — `POLICY.md` §3.
- **How** two touching owners delimit each other — `POLICY.md` §4.
- **How** the orchestrator discovers applicable owners —
  `POLICY.md` §5.

This file defines **what counts as proof** and **how proof travels**.
Nothing else.

---

## Appendix A — changes since v1.0.0

- **v1.4.0** — Full plugin translated into English. No semantic
  change; `evidence-schema: 1.3.x` unchanged (compatibility across the
  translation is guaranteed — no field renamed, no rule changed; only
  prose translated).
- **v1.3.0** — Three defects closed:
  - **C1**: `code-review-runtime` recovers six canonicals — three
    v1.2.0 had removed for preconditions (`build-passes`,
    `tests-pass`, `types-check`) and three new review checks
    (`test-strength`, `risk-proof-matrix`, `tests-that-never-run`).
    The owner stops collapsing into "someone emitted something".
  - **C2**: "no-canonicals fallback" removed from `coverage-complete`
    (§7.1) and replaced by rule 4.3.3: an owner without canonicals
    registered in §7.4 reports `BLOCKED (—/?)`. Registration in §7.4
    becomes a precondition for closing any `coverage-complete` gate.
  - **C3**: §7.5 rewritten as "`audit-app` does not execute
    commands". Preconditions cease to exist as a concept;
    `build-passes`, `tests-pass`, `types-check` become normal
    canonical checks of `code-review-runtime` (the owner produces
    them, inside its own harness). The v1.2.0 `gates.json.preconditions`
    renames to `adapter-hints:` in POLICY §5.1 and is read only by
    local adapters, never by the orchestrator. Closes the vector of
    arbitrary execution driven by the target — restores the
    read-only doctrine of the original `auditar-app`.
- **v1.2.0 + 1.2.1** — bilateral delimitation as a phase gate; the
  §5.1 fallback fixed from silent PASS to non-applicability with
  reason; §2.4.1 editorial guidance for skill meta-auditors absorbing the
  semantic part §3.5 stopped trying to verify mechanically.
- **v1.1.0** — §1.3 now cites the mechanical mechanism
  (`instruments.yaml` + §4.5) instead of v1.0.0's unverifiable
  promise.
- **v1.0.0** — first version of the contract. Establishes the
  seven-unit vocabulary, rule vs instrument, evidence schema,
  file-based collection channel, six-level severity taxonomy, semver
  compatibility rules, and declarative gate syntax. No migration from
  a previous version — the `production-quality-ready` plugin is born here.
