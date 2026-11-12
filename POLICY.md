# POLICY — the `production-quality-ready` marketplace

Governance of the five plugins: `production-quality-ready` (the base:
`bootstrap-project` with the cycle rules and adapter contracts, the audit
owners, `ship`, `CONTRACTS.md`, the runner and the gates) and the four that
depend on it, one per kind of project: `pqr-website`, `pqr-desktop`,
`pqr-ui-system` and `pqr-process`. **Authoritative** on: who owns which subject, when a
skill activates, how it composes with a local adapter, how conflicts
between owners are resolved.

Cross-references:

- What counts as evidence, gate machinery, schemas →
  `plugins/production-quality-ready/CONTRACTS.md`.
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

`commercial-readiness` (activation, first run, legal) and `design-pro`
(one guide per UX domain) work this way: neither pays permanent context
beyond its own `description`.

### 1.2 Bilateral delimitation

Whenever two owners touch the same subject (one as rule, another as
instrument, or two adjacent sub-topics), each `SKILL.md` **names the
other** in the `description` or in its Boundaries section.

Pairs that touch (skills only; the cycle steps are each project's own
skills, written by `bootstrap-project`, and a plugin skill names them by role
— "the project's review skill"). `tests/docs/test_docs_coherent.py` fails
when either side of a pair stops naming the other:

| Pair | How they delimit |
|---|---|
| `design-pro` ↔ `ui-system` | design-pro: "don't build the DS — ui-system"; ui-system: "UX/a11y verdict — design-pro" |
| `design-pro` ↔ `audit-app` | design-pro: "full app audit — audit-app"; audit-app: "single screen — design-pro" |
| `code-audit` ↔ `security-audit` | code-audit: "the adversary, CVEs — security"; security: "shape of the contract — code-audit" |
| `release-audit` ↔ `security-audit` | release: "vulnerable deps — security"; security: "signing, SBOM, deploy — release" |
| `commercial-readiness` ↔ `design-pro` | commercial: "onboarding UX — design-pro"; design-pro: "activation, checkout — commercial" |
| `reliability-audit` ↔ `security-audit` | reliability: "malicious corruption — security"; security: "accidental corruption — reliability" |
| `audit-app` ↔ `audit-website` | audit-app: "public web surface — audit-website"; audit-website: "software behind login — audit-app" |
| `spec` ↔ `diagnose` | spec: "broken behaviour — diagnose"; diagnose: "new behaviour — spec" |
| `reliability-audit` ↔ `diagnose` | reliability: "finding one cause — diagnose"; diagnose: "failure handling in production — reliability-audit" |
| `grill` ↔ `spec` | grill: "writes what the interview settles — spec"; spec: "runs the interview — grill" |
| `slice` ↔ `map` | slice: "the route is not visible yet — map"; map: "the route is already clear — slice" |
| `ship` ↔ `release-audit` | ship: "owns the release rules — release-audit"; release-audit: "executes them — ship" |
| `triage` ↔ `diagnose` | triage: "turns a report into a reproduction — diagnose"; diagnose: "decides what enters the queue — triage" |
| `improve` ↔ `code-audit` | improve: "owns the budgets and their verdict — code-audit"; code-audit: "plans against them — improve" |

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

A skill wakes when its `description` matches the task — the host's model
picks it, or the user or harness names it. **Never because another skill
called it.**

Every owner is **model-invoked**; two skills are **user-invoked**, because
an automatic trigger can cost more than it saves: `bootstrap-project`
writes adapters into a repo and a re-run rewrites what an earlier run
wrote, and `ship` acts on production, where the person owns that decision.
Both say so in their `description` ("User-invoked only.") and carry
`policy.allow_implicit_invocation: false` in `agents/openai.yaml` (Codex);
the user reaches each by name in either harness.

This is why every `description` says *when* (after writing code, at the
start of a conversation), not only *what*: the trigger is the only
router.

### 2.2 `audit-app` — finds by judgement, decides in code

`audit-app` doesn't invoke other skills. Finding is judgement: the owners'
instruments run (`run_all_owners.py`), the H/V/T/C reading adds evidence
files. Deciding is code: `apply_gates.py` reads `.audit/`, validates each
file against `CONTRACTS.md`, computes coverage `BLOCKED/PARTIAL/COMPLETE (n/m)`
and applies the gates. The model does not overrule its output; it adds
evidence and runs it again.

If an owner's evidence is missing, the verdict says `BLOCKED (n/m)` for it.
**`audit-app` does not activate the owner.** It names what is missing.

`apply_gates.py` runs no command against the audited repo (`CONTRACTS §7.5`).
`run_all_owners.py` does — the commands the project itself declared in its
`gates.json`, on the project's machine.

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
| `drive-app-window` | Technical capability (Win32/WebView2). *Used* to prove a change on desktop; emits artefacts, not verdicts. |
| `bootstrap-project` | Generator. Writes `gates.json` and the project's cycle skills. Not an auditor. |
| `spec` | Writer of requirements. Writes the spec file; closes no check. |
| `diagnose` | Finder of causes. Writes the reproduction and the regression test, and fixes at the cause; closes no check. |
| `grill` | Interview. Settles decisions in conversation; closes no check. |
| `slice` | Breakdown. Writes slices and their blocking edges; closes no check. |
| `map` | Chart. Writes the map and its decision tickets; closes no check. |
| `triage` | Intake. Moves issues through states and writes briefs; closes no check. |
| `handoff` | Packaging. Writes the pull-request body or the session handoff; closes no check. |
| `ship` | Release execution. Acts on production by the project's ship skill; emits artefacts (deploy log, smoke output); closes no verdict. |
| `improve` | Refactor plan. Writes the ranked plan; closes no check. |

The audit owners (core) correct nothing and publish nothing. Three skills
act, each by name or on a change the person asked for: `diagnose` fixes at
the cause, `ui-system` writes design-system code, `ship` deploys.

---

## 3. The project's cycle skills

The work cycle — open, review, close, verify, ship — is **the project's own
skills**, not plugin skills. The base plugin carries the rules
(`skills/bootstrap-project/references/universal/*/RULE.md`) and the shape each
project skill must have (`adapter-contracts/*.md`); `bootstrap-project` writes
the skills into the project.

### 3.1 Self-contained

A project skill carries its steps and works with no plugin loaded — in a
cloud session, in CI, on another machine. Its frontmatter is the host's:
`name`, `description`, `allowed-tools`; no `extends:` or `contract:`, which no
host implements. It points at the agent map (`CLAUDE.md`/`AGENTS.md`) for
what that already says — the agent map is always in context, a copy drifts.

An instrument this plugin ships carries its own proof of teeth: a red case
under `tests/` where it must fail (`CONTRACTS §4.6.4`). No red case, no gate.

### 3.2 Location and name

`<host>/skills/<local-name>/` inside the project, where `<host>` is `.agents`
or `.claude`. It travels with the project's commits. **The name is its own**,
never the rule's (`start-work`, `review-change`…), recorded in `gates.json`
under `owners.<rule>.adapter`: two skills with one short name leave the host
to pick by chance. It is written in the language of the project's agent map.

### 3.3 Division of responsibility

The rule owns the ordered steps and what never changes. The project skill
owns the paths, the commands, the *Where to look* table that makes review
proportional, the pointer to the invariants the project already paid for, and
the traps no rule covers. It cannot rewrite the rule or assert facts about
other projects.

---

## 4. Bilateral delimitation (mechanical)

**Rule 4.1.** For each pair `(A, B)` in the §1.2 table, `A`'s
`description` or Boundaries names `B`, and `B`'s names `A`. Missing on
either side = the *pair* fails, not the file.

**Rule 4.2.** Adding a subject that touches an existing one (or
splitting an existing owner) adds a row to §1.2 and the bilateral
refactor ships in the same release.

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
  "platform": "web",                       // web | desktop | both — required
  "sales-model": "subscription",           // licensed | subscription | both
  "stack": ["typescript", "hono", "d1"],
  "owners": {
    "code-audit": { "adapter": "code-audit.local.md" },
    "security-audit": { "threat-model": "docs/threat-model.md" },   // only when not at a usual path
    "reliability-audit": { "migrations-dir": "db/migrations" },     // default: migrations
    "audit-website": { "target": "https://example.com" },           // a URL, or a built folder
    "drive-app-window": { "not-applicable": "web app; verify uses browser automation" },
    "review-change": { "adapter": "myapp-review-change" },   // local name of the adapter skill
    "ui-system": { "ignore-dirs": ["servidor"] },      // passed to audit_ui.py as --ignore-dir
    "…": "…"
  },
  "adapter-hints": {
    "build-command": "npm run build",
    "tests-command": "npm test",
    "typecheck-command": "npm run typecheck",
    "smoke-command": "npm run smoke",
    "migrations-verify-command": "node scripts/verify-migrations.mjs"
  },
  "gates": ["release-candidate", "production-ready", "sellable"]
}
```

**Rule 5.1.1 (declared scope).** Every plugin owner is listed. An
inapplicable owner declares `not-applicable: "<reason>"`; one check that
does not apply is declared under its owner as
`not-applicable-checks: {"<check>": "<reason>"}` (`CONTRACTS §4.3.4`).
Omitting an owner is a defect of the file: `audit-app` aborts with
`owner-undeclared: <slug>`.

Reason: "silent omission" is silent PASS. Rule inherited from
`auditar-app`.

**Rule 5.1.2 (`adapter-hints:`).** The `adapter-hints:` section is
**metadata for producers that emit their own evidence** — the local
cycle skills and `scripts/run_all_owners.py`, which runs the declared
commands and writes `.audit/code-audit/*` with `command:` + `log:`.
`audit-app` **never reads it**. Not runnable commands from
`audit-app`'s point of view. The keys the runner reads, and the check
each one settles, are the table of `CONTRACTS §7.5.4`; a command under
any other key settles nothing.

**Rule 5.1.3 (platform).** `platform:` is required. Owners and checks
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

One version **value**, carried by the root `plugin.json` (hosts that do
not read `.claude-plugin/`), every `plugins/*/.claude-plugin/plugin.json`
and `.claude-plugin/marketplace.json`. CI asserts they are equal, so the
value cannot drift (`CONTRACTS §6.4`). Skills,
adapters, `gates.json` and evidence carry none: they name files, and the
file is the rule.

When the plugin starts requiring something a project file lacks, the
absence is the signal — `owner-undeclared`, `platform-undeclared`,
`missing-*` — and re-running `bootstrap-project` proposes the diff.

---

## 7. Non-goals

In `PURPOSE.md §7`. One addition that is policy, not purpose: where a
check requires seeing the app run and the harness cannot, the owner
reports `NOT_VERIFIED` with `needs-human`. It doesn't guess.
