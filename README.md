# production-quality-ready

Quality plugin that moves an app from *"works"* to *"can be sold"* —
for **web** (Workers, Next, SvelteKit, SSR…) and **desktop** (Tauri,
Electron, native) alike. No skill invokes another; every verdict is a
file with a command and a log behind it.

Read first:

- [`PURPOSE.md`](PURPOSE.md) — what the plugin is for, what counts as well made.
- [`POLICY.md`](POLICY.md) — who owns what.
- [`CONTRACTS.md`](CONTRACTS.md) — what counts as proof.

## The idea in one paragraph

The plugin is **generic**; your project is **not**. So the plugin ships
generic *owners* (security, reliability, code review, design, release,
commercial, website) and a generic *work cycle* (start → review → close
→ verify), and the **first skill you run — `bootstrap-project` — writes
the four project adapters** that give the cycle your real commands,
your real invariants, your test credentials and your surfaces. The
owners then bite on your codebase instead of on an imagined one.

## Install

Copy or clone into the host's plugin folder of the target repo:

```bash
# OpenCode / Antigravity / Codex — .agents
git clone https://github.com/JoaoPeixoto72/production-quality-ready.git .agents/plugins/production-quality-ready

# Claude Code — .claude, or via marketplace
git clone https://github.com/JoaoPeixoto72/production-quality-ready.git .claude/plugins/production-quality-ready
/plugin marketplace add JoaoPeixoto72/production-quality-ready
/plugin install production-quality-ready@JoaoPeixoto72/production-quality-ready
```

One-liners (`-Global` / `--global` for machine-wide):

```powershell
irm https://raw.githubusercontent.com/JoaoPeixoto72/production-quality-ready/main/install.ps1 | iex
```
```bash
curl -fsSL https://raw.githubusercontent.com/JoaoPeixoto72/production-quality-ready/main/install.sh | bash
```

## First command

```
use the bootstrap-project skill
```

It detects host (`.agents` / `.claude`), platform (`web` / `desktop` /
`both`), stack and commands, asks only what code cannot tell (name,
invariants you already paid for, test credentials), and writes:

- `<host>/gates.json` — platform, sales model, applicable owners, `adapter-hints`.
- `<host>/skills/<local-name>/SKILL.md` × 4 — **pre-filled** adapters of start-work, review-change, close-work and verify, each under a name of its own.
- `ESTADO.md` (state) and `AGENTS.md`/`CLAUDE.md` (map) if missing.

## Daily loop

| When | Skill | What it does |
|---|---|---|
| Start of a conversation | `start-work` | reads `ESTADO.md`, runs baseline, names the owner of the code you are about to touch; a bug is reproduced first |
| After writing code | `review-change` | full diff → local invariants → adversarial matrix for your platform → proof commands → argue against the approval → verdict |
| Need to *see* it | `verify` | launches the app, drives the flow (browser automation or `drive-app-window`), captures before/after |
| End of session | `close-work` | rewrites `ESTADO.md`; one subject, one owner; numbers carry command + HEAD |

## Audit loop (when you want to ship or sell)

```powershell
pwsh <plugin>/scripts/run-all-owners.ps1 -RepoRoot . [-WebsiteUrl https://…]
```

Runs every instrument the plugin can run for your platform — build,
typecheck, tests, `audit_ui.py`, `npm audit`/`cargo audit`, `gitleaks`,
lockfile/SBOM checks, migration verifier, website engines — and writes
`.audit/<owner>/*.evidence.yaml`. **A PASS is written only for a check
it executed, with `command:` and `log:`.** What it cannot run is
`NOT_VERIFIED/missing-instrument` — declared, not hidden.

Then:

```
use the audit-app skill
```

`audit-app` reads `.audit/`, validates every file (`validate_evidence.py`
— a PASS without a trace is downgraded), applies the gates
(`release-candidate`, `production-ready`, `sellable`) and writes
`docs/auditorias/<date>-<scope>.md`. Owners with no evidence show
`BLOCKED (n/m)`; that is the honest state, not a bug.

## The skills

| Skill | Role | Platforms | Runs code? |
|---|---|---|---|
| `bootstrap-project` | generator — **run first** | both | writes files |
| `start-work` · `review-change` · `close-work` | work cycle (adapters per project) | both | proof commands |
| `verify` | prove in the running app | both | browser driver / `gui.ps1` |
| `drive-app-window` | Win32/WebView2 driver for `verify` | desktop | `scripts/gui.ps1` |
| `code-review` | runtime + contracts + maintainability (size, nesting, params, ratchet) + perf budgets | both | build/test runners, `quality_scan.py` |
| `security-audit` | ASVS 5.0 + threat model; tenants, input, CVEs, secrets | both | dep/secret scanners |
| `reliability-audit` | persistence, migrations, crash; diagnosability (logs, PII) | both | harnesses (project) |
| `design-pro` | UX, WCAG 2.2 AA verdict, i18n | both | — (consumes ui-system, verify) |
| `ui-system` | OKLCH tokens, `data-ui` contract, `audit_ui.py`; React pack optional | both | `scripts/audit_ui.py` |
| `release-audit` | reproducible build, lockfiles, SBOM; signing (desktop), deploy/rollback (web) | both | ci/sbom checks |
| `commercial-readiness` | SELL-01..06 for licensed and subscription; legal; SLA | both | billing/licensing harness |
| `audit-website` | 360º + deep SEO/GEO engines, SARIF | web | `run_website_audit.mjs`, `seo/run_seo_audit.mjs` |
| `audit-app` | read-only orchestrator | both | `validate_evidence.py` |

Checks tagged for the other platform resolve `NOT_APPLICABLE/platform`
automatically — a Tauri app is not asked about cookies, a Worker is not
asked about installer signatures.

## Structure

```
production-quality-ready/
├── PURPOSE.md · POLICY.md · CONTRACTS.md · PLAN.md · README.md
├── adapter-contracts/        # what each project adapter must provide
├── scripts/
│   ├── measure-descriptions.py    # exit 1 if any description > 250 chars
│   └── run-all-owners.ps1         # runs instruments, writes evidence (PASS ⇒ command+log)
└── skills/                   # one folder per skill: SKILL.md + instruments.yaml (platforms:)
    ├── audit-app/scripts/validate_evidence.py   # mechanical evidence validator + tests
    ├── audit-website/{scripts,seo}/             # two engines
    ├── ui-system/{assets,packs/react-components,scripts}/
    └── bootstrap-project/templates/             # gates.json, AGENTS.md, ESTADO.md, 4 adapters
```

## Verify the plugin itself

```bash
python scripts/measure-descriptions.py skills                     # exit 1 if any description > 250
python -m unittest discover -s tests/audit-app -p "test_*.py"     # evidence + report validators
python -m unittest discover -s tests/code-review -p "test_*.py"   # quality_scan
pwsh scripts/run-all-owners.ps1 -RepoRoot <repo> -DryRun          # lists owners for the platform
```

## What NVIDIA SkillSpector says about these skills

Every skill here was scanned with [SkillSpector](https://github.com/NVIDIA/SkillSpector)
2.11.2 (`--no-llm`) through [skill-auditor](https://github.com/JoaoPeixoto72/skill-auditor)
5.3.0 (`audit.sh <skill> --strict`). **None is rejected and none gets a
`CRITICAL` finding.** Eight are eligible; seven are held for a person to look
at, and this is why — each one is a pattern the scanner flags on sight, not
behaviour that harms anyone:

| Skill | What the scanner flags | What it actually is |
|---|---|---|
| `code-review` | `subprocess` in `quality_scan.py` | one `git` call with a fixed argument list and no shell, to list the files git would commit and the files a change touched |
| `release-audit` | `subprocess` in `ci_inspection.py` | one read-only `git log -1` on the changelog, to date it |
| `security-audit` | `subprocess` in `secret_scan.py` | looks for committed secrets in the history — `gitleaks` when installed, otherwise `git log -p` with its own rules; that is its job |
| `audit-website` | network access; one file too long for its parser | it audits a public website, so it fetches that website; the URL is the one you give it |
| `reliability-audit` | "obfuscated text" in `migration_harness.py`; "autonomous decisions" in `log_inspection.py` | the text is em dashes in comments and SQLite's `executescript`, applying migrations to a throwaway database; the "decision" is a line in a report |
| `design-pro` | mixed-script Unicode; "autonomy", "persistence" and "scope" in the references | `ΔL` (the OKLCH luminance difference, Greek delta) in the text; UX guidance *about* AI features, offline fallbacks and review scope |
| `ui-system` | a metadata YARA rule on the description; mixed-script Unicode; one component too long for its parser | the description names an executable instrument (`audit_ui.py`); `ΔL` again |

SkillSpector reads text for patterns and cannot tell a skill that *documents*
or *runs a fixed tool* from one that misuses it — its README lists that limit.
A hold is a request for a person to read the flagged line, which is what this
table does.

## What it does NOT

- **Correct anything.** It audits. Correction is another session.
- **Publish, bump versions, tag.**
- **Write a PASS from reading code.** CONTRACTS §4.6.
- **Replace looking at the running app.** It forces you to say when you did not.

## Licence

Apache-2.0 © 2026 Joao Peixoto unless a file states otherwise.
