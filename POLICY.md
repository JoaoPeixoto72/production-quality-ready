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

`commercial-readiness` (activation, first run, legal) and `design-pro`
(one guide per UX domain) work this way: neither pays permanent context
beyond its own `description`.

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

A skill wakes when its `description` matches the task — the host's model
picks it, or the user or harness names it. **Never because another skill
called it.** No skill sets `disable-model-invocation`: the plugin
publishes nothing and deletes nothing, so there is no skill whose
automatic trigger costs more than it saves.

This is why every `description` says *when* (after writing code, at the
start of a conversation), not only *what*: the trigger is the only
router.

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

The alternative — an orchestrator that invokes every owner on its
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
carries `extends: production-quality-ready:<name>`. Without an adapter,
the universal skill returns `NOT_VERIFIED/missing-adapter`
(`CONTRACTS §4.5`).

Contract for each adapter lives in `adapter-contracts/<name>.md` at
the plugin root — required frontmatter, required body sections, what
the adapter does not do.

### 3.2 Location of the adapter

Local adapter lives in `<host>/skills/<local-name>/` inside the target
repo, where `<host>` is `.agents` (OpenCode, Antigravity, Codex…) or
`.claude` (Claude Code). `bootstrap-project` detects the host. It travels
with the project's commits. Its version is independent of the plugin's;
it declares which `extends` it inherits from.

**The local name differs from the plugin skill's name** (`<project>-start-work`,
or a verb in the project's language) and is recorded in
`gates.json` under `owners.<skill>.adapter`. Two skills with the same
short name leave the host to pick one by chance — usually the generic
one, which has no commands.

The adapter's `contract:` names the file, never a copy or a version:
`production-quality-ready/CONTRACTS.md`. A copy in the project would be
a second owner of the contract, and it drifts the day the plugin
updates.

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
    "code-review": { "adapter": "code-review.local.md" },
    "security-audit": {},
    "audit-website": { "target": "https://example.com" },
    "drive-app-window": { "not-applicable": "web app; verify uses browser automation" },
    "review-change": { "adapter": "rever-mudanca" },   // local name of the adapter skill
    "ui-system": { "ignore-dirs": ["servidor"] },      // passed to audit_ui.py as --ignore-dir
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

One version, in `.claude-plugin/plugin.json` — the host reads it to
offer an update (`CONTRACTS §6`). Skills, adapters, `gates.json` and
evidence carry none: they name files, and the file is the rule.

When the plugin starts requiring something a project file lacks, the
absence is the signal — `owner-undeclared`, `platform-undeclared`,
`missing-*` — and re-running `bootstrap-project` proposes the diff.

---

## 7. Non-goals

In `PURPOSE.md §7`. One addition that is policy, not purpose: where a
check requires seeing the app run and the harness cannot, the owner
reports `NOT_VERIFIED` with `needs-human`. It doesn't guess.
