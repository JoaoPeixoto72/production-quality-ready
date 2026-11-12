# production-quality-ready

Quality plugins that move an app from *"works"* to *"can be sold"* —
for **web** (Workers, Next, SvelteKit, SSR…) and **desktop** (Tauri,
Electron, native) alike. No skill invokes another; every verdict is a
file with a command and a log behind it, and the gates are decided by
code, not by a model.

Read first:

- [`PURPOSE.md`](PURPOSE.md) — what the plugins are for, what counts as well made.
- [`POLICY.md`](POLICY.md) — who owns what.
- [`CONTRACTS.md`](plugins/production-quality-ready/CONTRACTS.md) — what counts as proof.
- [`rules/writing-for-agents.md`](rules/writing-for-agents.md) — how to write anything an agent reads.
- [`tests/instruments/`](tests/instruments/) — the red case of every instrument: the fixture where it must fail.

## Five plugins, one marketplace

The base is the machine every project runs: the skills in it hand work to
each other and cannot be installed apart. Each of the other four is an island
for one kind of project; it declares the base in `dependencies`, so installing
it brings the base along. A project pays context only for the descriptions of
what it installs.

| Plugin | Install it for | What it holds |
|---|---|---|
| `production-quality-ready` (base) | every project | `bootstrap-project` (the cycle rules and adapter contracts it writes from), `audit-app` and the audit owners (`code-audit`, `security-audit`, `reliability-audit`, `release-audit`, `commercial-readiness`, `design-pro`), `ship`, `run_all_owners.py`, `apply_gates.py`, `CONTRACTS.md` |
| `pqr-website` | a public site (Astro, any static build) | `audit-website` (SEO, GEO, Core Web Vitals, cookies) |
| `pqr-desktop` | a native desktop app on Windows (Tauri, WebView2) | `drive-app-window` (Win32/WebView2 driver) |
| `pqr-ui-system` | a project that adopts the `data-ui` design system | `ui-system` (OKLCH tokens, `data-ui` contract, `audit_ui.py`) |
| `pqr-process` | planning the work before the code | `spec`, `grill`, `map`, `slice`, `triage`, `diagnose`, `improve`, `handoff` |

## Install

Claude Code:

```
/plugin marketplace add JoaoPeixoto72/production-quality-ready
/plugin install production-quality-ready@production-quality-ready
```

From a shell (a cloud session, CI), the same two steps are
`claude plugin marketplace add JoaoPeixoto72/production-quality-ready` and
`claude plugin install production-quality-ready@production-quality-ready`.
`claude plugin details <plugin>@production-quality-ready` prints what each
plugin costs in context.

Other hosts: clone, then link the skills of the plugins you want.

```bash
git clone https://github.com/JoaoPeixoto72/production-quality-ready.git .agents/plugins/production-quality-ready
bash scripts/link-skills.sh --plugins production-quality-ready,pqr-website   # or: pwsh scripts/link-skills.ps1 -Plugins …
```

**Codex reads `.agents/skills`, not `.agents/plugins/`**, so the link step
is what makes the skills visible there. `install.ps1 -Codex` and
`install.sh --codex` do it in the same run.

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

It detects host (`.agents` / `.claude`), platform, stack and commands, asks
only what code cannot tell (name, invariants you already paid for, test
credentials, how a change reaches production), and writes:

- `<host>/gates.json` — platform, sales model, applicable owners, `adapter-hints`.
- `<host>/skills/<local-name>/SKILL.md` — the project's own **start, review,
  close, verify and ship** skills, each under a name of its own. They are
  self-contained: they work with no plugin loaded (cloud sessions, CI,
  another machine), and they point at the project's agent map for the
  invariants instead of copying them.
- `ESTADO.md` (state) and `AGENTS.md`/`CLAUDE.md` (map) if missing.

## Daily loop (the project's skills)

| When | Skill | What it does |
|---|---|---|
| Start, before changing code | start | reads the state document, runs the cheapest baseline, names the owner of the code you are about to touch |
| After writing code | review | full diff; spec and standards as two verdicts; only the axes the diff touches; one proof run per state of the tree |
| Need to *see* it | verify | launches the app, drives the flow, captures before/after |
| End of session | close | rewrites the state document; pass/fail beside the command, no stored counts |
| To production | ship | the project's real deploy path, smoke, rollback, and what needs a person |

## Audit loop (when you want to ship or sell)

```bash
python <plugin>/scripts/run_all_owners.py --repo . [--website-url https://…]
```

Runs every instrument the plugin can run for your platform — the declared
build, typecheck and tests, `quality_scan.py`, `npm`/`pnpm`/`yarn`/`cargo`
audit, secret scan, lockfile/SBOM checks, migration verifier — and writes
`.audit/<owner>/*.evidence.yaml`. **A PASS is written only for a check it
executed, with `command:` and `log:`.** What it cannot run is
`NOT_VERIFIED/missing-instrument` — declared, not hidden. It ends by
running `apply_gates.py`, which validates every file and decides
`release-candidate`, `production-ready` and `sellable` (exit 0 open, 1
closed, 2 cannot judge). `--no-gates` stops before the verdict;
`--dry-run` lists the owners for the platform and writes nothing.

Then, for the reading only a person or a model can do:

```
use the audit-app skill
```

`audit-app` reads the code by the H/V/T/C method — flows (H), layers (V),
transitions (T) and the cross-audit (C) — and turns each backed finding
into an evidence file like any other. Then it runs `apply_gates.py` again
and pastes its output into the report. It never overrules the code's
verdict; it adds evidence.

Every skill is **model-invoked** except `bootstrap-project` and `ship`,
which the user names by hand (`POLICY.md §2.1`): the first writes into
the repo, the second acts on production.

Frontmatter follows the [Agent Skills](https://agentskills.io) spec
(`name`, `description`, `allowed-tools`), so a skill loads in any host.
Each skill carries `agents/openai.yaml` for Codex's skill picker; Claude
Code reads `SKILL.md` alone.

## Structure

```
production-quality-ready/
├── PURPOSE.md · POLICY.md · README.md
├── .claude-plugin/marketplace.json   # the five plugins
├── rules/                            # source of the rule copies each plugin carries
├── scripts/                          # link-skills.* (hosts that read .agents/skills)
├── plugins/
│   ├── production-quality-ready/     # CONTRACTS.md, adapter-contracts/, scripts/{run_all_owners,measure-descriptions}.py, skills/<owner>/
│   │   ├── skills/audit-app/scripts/ # apply_gates.py, validate_evidence.py, validate_report.py
│   │   └── skills/bootstrap-project/ # references/universal/<rule>/, templates/
│   ├── pqr-website/ · pqr-desktop/ · pqr-ui-system/ · pqr-process/
└── tests/                            # one red case per instrument, gates, runner, docs coherence
```

## Verify the plugins themselves

```bash
python plugins/production-quality-ready/scripts/measure-descriptions.py plugins      # exit 1 if any description > 250
python -m pip install pytest && python -m pytest tests -q
python plugins/production-quality-ready/scripts/run_all_owners.py --repo <repo> --dry-run
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
| `code-audit` | `subprocess` in `quality_scan.py` | one `git` call with a fixed argument list and no shell, to list the files git would commit and the files a change touched |
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

## Which stacks the instruments know

The rules are stack-neutral. The instruments are not, and where one does not
know a stack it says `NOT_VERIFIED` with the reason — never a `PASS` or a
`FAIL` it did not measure.

| Stack | Runs on its own | The project declares (`CONTRACTS §7.5.4`) |
|---|---|---|
| Node (npm, pnpm, yarn), web | build, typecheck and tests; the package manager's audit; lockfile tracked; `quality_scan` over TS/JS, Svelte, Vue and Astro; webhook idempotency; SQL migrations applied to a throwaway SQLite | smoke, accessibility capture, tenant isolation, billing paths |
| Rust (Cargo), Tauri desktop on Windows | build, typecheck and tests; `cargo audit` when installed; `Cargo.lock` tracked; `quality_scan` over `.rs`; `drive-app-window` | signing and updater checks, the crash harness |
| Sites (Astro and any static build) | `audit-website` over the built folder or the URL | the target |
| Anything else | the commands `adapter-hints` declares | every other check stays `NOT_VERIFIED` until an instrument for that stack exists |

## What it does NOT

- **Correct anything while auditing.** The audit owners judge; `diagnose`
  and `improve` (pqr-process) and `ship` act, each on a request of its own.
- **Write a PASS from reading code.** CONTRACTS §4.6.
- **Replace looking at the running app.** It forces you to say when you did not.

## Licence

Apache-2.0 © 2026 Joao Peixoto unless a file states otherwise.
