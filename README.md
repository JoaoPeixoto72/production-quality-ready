# production-quality-ready

Quality plugin to move an app from *"works"* to *"can be sold"*.
Independent owners; each skill wakes when called; none invokes another.

Read first:

- [`PURPOSE.md`](PURPOSE.md) — what the plugin is for, what counts as
  well made.
- [`POLICY.md`](POLICY.md) — who owns what.
- [`CONTRACTS.md`](CONTRACTS.md) — what counts as proof.

## Install

### 1. Claude Code

**Option A — Via Claude Code Marketplace (Recommended):**
In your Claude Code terminal session:
```bash
/plugin marketplace add JoaoPeixoto72/production-quality-ready
/plugin install production-quality-ready@JoaoPeixoto72/production-quality-ready
```

**Option B — Run directly with local plugin directory:**
```bash
claude --plugin-dir /path/to/production-quality-ready
```

---

### 2. Antigravity

**Option A — Project Workspace (Recommended):**
Clone or copy into `.agents/plugins/production-quality-ready` at the root of your project:
```bash
git clone https://github.com/JoaoPeixoto72/production-quality-ready.git .agents/plugins/production-quality-ready
```

**Option B — Machine-Global:**
Clone into your global Antigravity config directory:
```bash
# Windows
git clone https://github.com/JoaoPeixoto72/production-quality-ready.git "$HOME/.gemini/config/plugins/production-quality-ready"

# Linux / macOS
git clone https://github.com/JoaoPeixoto72/production-quality-ready.git ~/.gemini/config/plugins/production-quality-ready
```

---

### 3. One-Liner CLI Installer

Run this in the root of any target project workspace:

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/JoaoPeixoto72/production-quality-ready/main/install.ps1 | iex
```

**Linux / macOS / WSL (Bash):**
```bash
curl -fsSL https://raw.githubusercontent.com/JoaoPeixoto72/production-quality-ready/main/install.sh | bash
```

*(Add `-Global` or `--global` to install globally).*

---

### 4. Setup in Target Project

Once installed, inside your project with the agent active:
```
"use the bootstrap-project skill"
```

The `bootstrap-project` asks the essentials (name, invariants, build /
test commands) and writes:

- `.claude/gates.json` — gate pack with applicable owners marked.
- `CLAUDE.md`, `ESTADO.md` — map and current state of the project.
- `.claude/skills/{start-work, review-change, close-work, verify}/` —
  4 local adapter skills that cite the plugin's universal owners.
- `.claude/CONTRACTS.md.snapshot` — copy of the contract so adapters
  resolve `contract:` without depending on the global install path.

## First command

After bootstrap:

```
# in the agent
"run audit-app"
```

`audit-app` discovers applicable owners via `gates.json`, reads
existing evidence in `.audit/**/*.evidence.yaml`, applies declarative
gates, and writes `docs/auditorias/<date>-<scope>.md` with a
`Product × Coverage` verdict.

**A first run with no produced evidence returns `BLOCKED (0/m)` for
every owner** — that is expected; the output says exactly which checks
are missing. Each owner produces its evidence when explicitly invoked
by the user or the pipeline.

## Producing evidence — `run-all-owners.ps1`

`audit-app` is a **reader**; it never runs owners itself (PURPOSE §3.3
— evidence is a file, not a call). To actually populate `.audit/`,
run the shell orchestrator:

```powershell
# from the repo root, using pwsh (Windows/Linux/macOS)
pwsh <plugin>/scripts/run-all-owners.ps1 -RepoRoot .
```

It reads `.claude/gates.json`, walks every applicable owner, invokes
each owner's instrument (`ui-system::audit_ui.py`,
`code-review-runtime` build/test commands from `adapter-hints`, …),
and writes `.audit/<owner>/*.evidence.yaml` in schema 1.3.x. Owners
that need a project-local harness the plugin cannot ship (e.g. the
crash harness for `reliability-audit`, the clean-VM stopwatch for
`commercial-readiness`, the threat-model check for `security-audit`)
land as `NOT_VERIFIED/missing-instrument` — the gap is **declared**,
not silent.

This does not violate the "no invocation" rule: this is a shell
script running **outside** the model, producing files. The model-side
`audit-app` still only reads `.audit/`.

Flags:

- `-Only ui-system,seo-audit` — run just these owners.
- `-Skip commercial-readiness` — skip these owners.
- `-DryRun` — show what would run; write no files.
- `-PluginRoot <path>` — override plugin location (default: `..` of
  the script).

After `run-all-owners.ps1`, ask the agent to run `audit-app`; the
verdict now reflects real evidence.

## Structure

```
production-quality-ready/
├── PURPOSE.md              # what it's for
├── POLICY.md               # who owns what
├── CONTRACTS.md            # what counts as proof
├── PLAN.md                 # what was proposed, each correction
├── README.md               # this file
├── adapter-contracts/      # contract for local adapters
│   ├── start-work.md
│   ├── review-change.md
│   ├── close-work.md
│   └── verify.md
├── scripts/
│   ├── measure-descriptions.py   # context oracle
│   └── run-all-owners.ps1        # CI-side owner runner (see below)
└── skills/                 # the plugin's skills
    ├── audit-app/          # orchestrator (read-only)
    ├── code-review-runtime/
    ├── code-review-contract/
    ├── ui-system/
    ├── design-pro/
    ├── security-audit/
    ├── reliability-audit/
    ├── performance-audit/
    ├── observability/
    ├── release-audit/
    ├── commercial-readiness/
    ├── seo-audit/
    ├── start-work/         # work cycle
    ├── review-change/
    ├── close-work/
    ├── verify/             # visual proof
    ├── drive-app-window/   # technical capability
    ├── skill-auditor/      # meta
    └── bootstrap-project/  # generator
```

## Verify the plugin

Before installing, or after editing it:

```bash
# descriptions under the working ceiling (500 chars)
python3 scripts/measure-descriptions.py .

# zero mechanical findings
bash skills/skill-auditor/scripts/audit.sh skills

# validate-report tests
python3 skills/audit-app/scripts/test_validate_report.py
```

Pair-check (that every owner naming another in its description is named
back) is part of the linter above.

## What it does NOT

- **Does not correct anything.** Audits. Correction is another session.
- **Does not publish, does not bump versions, does not create tags.**
- **Does not replace human judgment** where the app must be seen
  running; what it does is force declaring when it wasn't seen.

See [`PURPOSE.md`](PURPOSE.md) §7 for the full list of non-goals.

## Licence

Apache-2.0 unless a file states otherwise. See `LICENSE` in every skill
that ships its own (e.g. `seo-audit`, `drive-app-window`).
