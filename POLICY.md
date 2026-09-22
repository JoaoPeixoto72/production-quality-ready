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
other** in the `description` or in its Boundaries section.

Pairs that touch:

| Pair | How they delimit |
|---|---|
| `design-pro` ↔ `ui-system` | design-pro: "don't build the DS — ui-system"; ui-system: "UX/a11y verdict — design-pro" |
| `design-pro` ↔ `audit-app` | design-pro: "full app audit — audit-app"; audit-app: "single screen — design-pro" |
| `code-review` ↔ `verify` | code-review: "proof in the running app — verify"; verify: "automated tests — code-review" |
| `code-review` ↔ `security-audit` | code-review: "the adversary, CVEs — security"; security: "shape of the contract — code-review" |
| `code-review` ↔ `review-change` | review-change is the pre-commit gate that cites code-review's checks; it does not re-declare them |
| `release-audit` ↔ `security-audit` | release: "vulnerable deps — security"; security: "signing, SBOM, deploy — release" |
| `commercial-readiness` ↔ `design-pro` | commercial: "onboarding UX — design-pro"; design-pro: "activation, checkout — commercial" |
| `reliability-audit` ↔ `security-audit` | reliability: "malicious corruption — security"; security: "accidental corruption — reliability" |
| `verify` ↔ `drive-app-window` | verify: "drive the window — drive-app-window"; drive-app-window: "what to prove — verify" |
| `audit-app` ↔ `review-change` | audit-app: "one PR — review-change"; review-change: "whole app — audit-app" |
| `audit-app` ↔ `audit-website` | audit-app: "public web surface — audit-website"; audit-website: "software behind login — audit-app" |
| `start-work` ↔ `review-change` | start-work: "review code — review-change"; review-change: "open a session — start-work" |
| `review-change` ↔ `close-work` | review-change: "update documents — close-work"; close-work: "review first — review-change" |
| `start-work` ↔ `close-work` | start-work: "close — close-work"; close-work: "open — start-work" |

The work-cycle pairs form a **triangle**, not a chain — a user can type
the wrong verb directly, not only the adjacent one. Every skill in the
cycle delimits against the other two.

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

1. Discovers applicable owners from the project's `gates.json` (`.agents/` or `.claude/`), filtered by `platform`.
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

| Skill | Purpose |
|---|---|
| `drive-app-window` | Technical capability (Win32/WebView2). *Used* by `verify` on desktop; emits artefacts, not verdicts. |
| `bootstrap-project` | Generator. Writes `gates.json` and the four project adapters. Not an auditor. |
| `start-work` / `close-work` | Work cadence. Read and rewrite the state document. |

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

Local adapter lives in `<host>/skills/<name>/` inside the target repo,
where `<host>` is `.agents` (OpenCode, Antigravity, Codex…) or `.claude`
(Claude Code). `bootstrap-project` detects the host. It travels with the
project's commits. Its version is independent of
the plugin's; it declares which `extends` it inherits from.

Two options for the `contract:` path (`bootstrap-project` step 5b):

- **Plugin installed globally** → absolute path to
  `production-quality-ready/CONTRACTS.md`. No duplication.
- **Local snapshot** → `bootstrap-project` copies `CONTRACTS.md` to
  `<repo>/<host>/CONTRACTS.md.snapshot`; the adapter uses
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

Rule written in POLICY §1.2. Verified by reading: each side of a pair
names the other.

**Rule 4.1.** For each pair `(A, B)` in the §1.2 table, `A`'s
`description` mentions `B` and `B`'s mentions `A`. Missing on either
side = the *pair* fails, not the file.

**Rule 4.2.** The §1.2 table is the declarative source. A reviewer of
a plugin change enumerates its pairs and checks that the token of the
other owner appears in the `description` or Boundaries of each side.

**Rule 4.3.** Adding a subject that touches an existing one (or
splitting an existing owner) adds a row to the table and requires a
bilateral refactor in the same release as the change.

---

## 5. Discovery by the orchestrator

`audit-app` needs to know which owners are applicable to the project.
In order:

### 5.1 Project gate pack

Source: `<repo-root>/.agents/gates.json` or `<repo-root>/.claude/gates.json`
(`.agents` wins if both exist). Structure (CONTRACTS §5.4):

```jsonc
{
  "plugin": "production-quality-ready",
  "plugin-version": "2.0.0",
  "platform": "web",                       // web | desktop | both — required
  "sales-model": "subscription",           // licensed | subscription | both
  "stack": ["typescript", "hono", "d1"],
  "owners": {
    "code-review": { "adapter": "code-review.local.md" },
    "security-audit": {},
    "audit-website": { "target": "https://example.com" },
    "drive-app-window": { "not-applicable": "web app; verify uses browser automation" },
    "…": "…"
  },
  "adapter-hints": {
    "build-command": "npm run build",
    "tests-command": "npm test",
    "typecheck-command": "npm run typecheck",
    "migrations-verify-command": "node scripts/verify-migrations.mjs"
  },
  "gates": ["release-candidate", "production-ready", "sellable"]
}
```

**Rule 5.1.1 (declared scope).** Every plugin owner is listed. An
inapplicable owner declares `not-applicable: "<reason>"`. Omitting an
owner is a defect of the file: `audit-app` aborts with
`owner-undeclared: <slug>`.

Reason: "silent omission" is silent PASS. Rule inherited from
`auditar-app`.

**Rule 5.1.2 (`adapter-hints:`).** The `adapter-hints:` section is
**metadata for producers that emit their own evidence** — the local
adapters and `scripts/run-all-owners.ps1`, which runs the declared
commands and writes `.audit/code-review/*` with `command:` + `log:`.
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

**Rule 5.1.5 (platform).** `platform:` is required. Owners and checks
whose `platforms:` exclude it are `NOT_APPLICABLE/platform` without
being listed as `not-applicable` by hand (CONTRACTS §3.5). Listing them
anyway, with a reason, is allowed and clearer.

### 5.2 Project-type detection

If no `gates.json`, `audit-app` tries detection by manifest files
(`Cargo.toml` or `tauri.conf.json` → `platform: desktop`; `package.json`
+ web framework or `wrangler.*` → `platform: web`; …) and tells the user
to run `bootstrap-project`, which writes the file.

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

The project's `gates.json` follows the plugin's major. Bumping the
plugin locally requires updating the file too; re-running
`bootstrap-project` proposes the diff.

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

- **v2.0.0** — Plugin made platform-agnostic; owners merged 22 → 15
  (`code-review-runtime` + `code-review-contract` + `performance-audit`
  → `code-review`; `observability` → `reliability-audit` §2;
  `seo-audit` → `audit-website/seo`); the three skill meta-auditors
  removed (tooling, not product). §1.2 pair table rewritten. §2.4.1
  removed with them. §3.2 and §5.1 become host-agnostic (`.agents` or
  `.claude`). §5.1 gains `platform`, `sales-model`, Rule 5.1.5.
  `bootstrap-project` declared the first skill to run.
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
  skill meta-auditors absorbing the semantic part `CONTRACTS §3.5` stopped
  trying to verify mechanically.
- **v1.1.0** — §1.3 now cites the mechanical mechanism
  (`instruments.yaml` + `CONTRACTS.md §4.5`) instead of the
  unverifiable promise of v1.0.0.
- **v1.0.0** — first version. Establishes the subject-authority table,
  local-adapter pattern, bilateral delimitation with mechanical
  pair-check, discovery by gate pack + detection + explicit activation,
  versioning rules, and non-goals. Compatible with
  `evidence-schema: 1.x`.
