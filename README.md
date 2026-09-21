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
    ├── skill-readiness-auditor/ # meta: instruction quality & triggers
    ├── skill-security-auditor/  # meta: security, injection & MCP
    ├── skill-release-gate/      # meta: enrolment & release decisions
    └── bootstrap-project/  # generator
```

## Detailed Guide to the 21 Skills

Each skill operates under strict boundaries defined in [`POLICY.md`](POLICY.md) and [`PURPOSE.md`](PURPOSE.md). No skill invokes another skill; all results are stored as immutable evidence files (`.audit/<owner>/*.evidence.yaml`).

---

### 1. `audit-app` — Central Quality & Sellability Orchestrator
- **Role:** Orchestrator (Strictly Read-Only).
- **Canonical Rule:** `CONTRACTS.md` — binary gates, no arbitrary numeric scoring (`94/100`), absence of evidence is never approval (`BLOCKED (n/m)`).
- **What it actually does:**
  - Reads the project-level gates file (`.claude/gates.json` or `.agents/gates.json`).
  - Scans all evidence generated in `.audit/<owner>/<producer>--<check>.evidence.yaml`.
  - Validates evidence integrity and authority against each owner'''s `instruments.yaml` via Python test harness (`validate_report.py`).
  - Applies standard gates (`release-candidate`, `production-ready`, `sellable`) and custom gates.
  - Generates the authoritative sellability audit report in `docs/auditorias/<date>-<scope>.md`.
- **What it does NOT do:** Never runs build commands or tests against the audited repo; strictly reads and aggregates pre-produced evidence files.

---

### 2. `bootstrap-project` — Project Generator & Scaffold
- **Role:** Project Scaffolder.
- **Canonical Rule:** Self-contained bootstrapping with zero implicit magic.
- **What it actually does:**
  - Generates the configuration files and local adapters required to onboard any codebase to `production-quality-ready`.
  - Generates:
    - `.claude/gates.json` (or `.agents/gates.json`): Declarative gate configuration with applicable owners and adapter-hints.
    - `CLAUDE.md` & `ESTADO.md`: Architecture map, invariant ledger, and state management.
    - Local adapter skills in `.claude/skills/` or `.agents/skills/`: `start-work`, `review-change`, `close-work`, `verify`.
    - `.claude/CONTRACTS.md.snapshot`: Frozen contract snapshot for offline adapter execution.
- **When to use:** When initializing or migrating a repository to use the quality system.

---

### 3. `start-work` — Work Cycle: Session Opening
- **Role:** Work Cycle Adapter (Universal Contract).
- **Canonical Rule:** Read state, confirm sound tree, identify canonical owner before touching code.
- **What it actually does:**
  - Checks git tree cleanliness, branch, and records baseline commit snapshot $t_0$.
  - Executes build and test suite to confirm baseline green health before any edits.
  - Reads `ESTADO.md` invariants to prevent re-inventing existing logic.
  - Identifies which canonical owner owns the subject of the upcoming changes.
- **When to use:** At the beginning of every coding session and before making modifications.

---

### 4. `review-change` — Work Cycle: Code Change Review
- **Role:** Work Cycle Adapter (Universal Contract).
- **Canonical Rule:** Review against project invariants and canonical owners before calling work done.
- **What it actually does:**
  - Analyzes `git diff` across 5 core dimensions:
    1. **Reuse vs. Reinvent:** Prevents duplicating utilities, styling tokens, or schemas.
    2. **Architectural Layers:** Verifies imports and boundary directions.
    3. **Contracts:** Ensures IPC, RPC, or API schema modifications are guarded by contract tests.
    4. **UI/UX Invariants:** Checks design tokens, focus states, and accessibility constraints.
    5. **Security & Data:** Ensures untrusted inputs are validated and sanitized.
- **When to use:** Right after code is written/modified, before committing and before running `close-work`.

---

### 5. `close-work` — Work Cycle: Session Closing & Documentation
- **Role:** Work Cycle Adapter (Universal Contract).
- **Canonical Rule:** *"One subject, one owner; reason stays, history goes."*
- **What it actually does:**
  - Enforces documentation boundaries in `ESTADO.md` and repository docs.
  - Preserves architectural rationale and design decisions (*"reason stays"*).
  - Prunes transient chronological logs and ephemeral chatter (*"history goes"*).
  - Records verified test evidence and new commit snapshot $t_1$.
- **When to use:** At the end of every work session, right before final commit/PR.

---

### 6. `verify` — Interactive Runtime Proof Strategy
- **Role:** Proof Strategy (Requires Local Adapter).
- **Canonical Rule:** Prove changes in the real, running application; automated tests alone do not prove visual and interactive reality.
- **What it actually does:**
  - Defines the verification procedure: launching dev server / native binary, driving specific user workflows, and capturing proof.
  - Uses `drive-app-window` (or browser automation) to execute clicks, typing, and capture before/after screenshots.
  - Compares visual and interactive results against expected specifications.
- **When to use:** Whenever proving interactive UI behavior, visual regression fixes, or desktop workflows.

---

### 7. `drive-app-window` — Desktop Window Automation Capability
- **Role:** Technical Capability (Win32 / WebView2 / Tauri / Electron).
- **Canonical Rule:** Coordinate-pinned automation with full-content capture; never closes verdicts independently.
- **What it actually does:**
  - Powered by native Windows PowerShell script `scripts/gui.ps1`.
  - Locates windows by title / process (via `EnumWindows` and `user32.dll`).
  - Pins window position and size $(0, 0, 1800, 1150)$ for deterministic coordinate targeting.
  - Sends native input actions: click, double click, keyboard typing, key chords, drag-and-drop, scroll.
  - Captures high-definition screenshots via `PrintWindow` (`PW_RENDERFULLCONTENT`) avoiding monitor bleed.
- **When to use:** Called as an instrument by `verify` or `design-pro` to automate native desktop applications.

---

### 8. `code-review-runtime` — Runtime Quality, Concurrency & Test Strength
- **Role:** Canonical Quality Owner.
- **Canonical Rule:** *"A test that has never failed proves nothing"* + zero silent panics + strict type soundness.
- **What it actually does:**
  - Audits runtime execution: thread safety, concurrency hazards, race conditions, memory leaks, channel deadlocks.
  - Audits cancellation handling: ensures abort controllers and cancellation tokens clean up background resources.
  - Measures test strength: verifies tests contain genuine oracles and assert on domain invariants rather than trivial mock outputs.
  - Evaluates bundle size and binary footprint against declared budgets.
- **Instruments:** `build-runner`, `test-runner`, `static-analysis`. Emits `runtime.build-passes`, `runtime.tests-pass`, `runtime.types-check`, `runtime.tests-have-oracles`, `runtime.concurrency-safe`.

---

### 9. `code-review-contract` — Architecture Boundaries, IPC & API Schemas
- **Role:** Canonical Quality Owner.
- **Canonical Rule:** Both sides of a contract must be cross-checked by tests exercising actual serialization, not by reading code.
- **What it actually does:**
  - Validates IPC / RPC / REST / GraphQL schemas crossing subsystem boundaries.
  - Enforces dependency direction (unidirectional dependencies, no reverse imports between layers).
  - Audits boundary resilience: declared timeouts, idempotent retry semantics, explicit failure modes.
  - Ensures schemas are backward- and forward-compatible.
- **Instruments:** `test-runner` (exercising contract roundtrips) and `static-analysis` (detecting inverted layer imports). Emits `contract.layer-direction`, `contract.schema-compat`, `contract.timeout-declared`, `contract.retry-idempotent`.

---

### 10. `security-audit` — Product Security & Vulnerability Analysis
- **Role:** Canonical Quality Owner.
- **Canonical Rule:** OWASP ASVS 5.0 + the application'''s declared threat model.
- **What it actually does:**
  - Audits trust boundaries, ingress validation, cryptographic implementations (PBKDF2, Argon2, timing-safe equality).
  - Checks least privilege / capabilities configuration (Tauri permissions, CSP headers, OS access limits).
  - Inspects dependency tree for known CVEs (`npm audit`, `cargo audit`).
  - Scans codebase for leaked credentials, secrets, and private keys.
  - Audits data-at-rest encryption and storage hygiene.
- **Instruments:** `threat-model-check`, `test-runner`, `dep-scanner`, `secret-scanner`, `crash-harness`. Emits `sec.threat-model-declared`, `sec.auth-strength`, `sec.capabilities-min`, `sec.csp-strict`, `sec.deps-no-cve`.

---

### 11. `reliability-audit` — Persistence, Atomic Writes & Migrations
- **Role:** Canonical Quality Owner.
- **Canonical Rule:** Zero data loss on crashes; migrations from **every** published version must succeed.
- **What it actually does:**
  - Audits write paths to guarantee atomic commits (temp file + atomic replace or ACID DB transactions).
  - Verifies behavior under crash scenarios (crash-mid-write harness).
  - Validates database migration chain: forward migrations from v0 to HEAD without data corruption.
  - Verifies graceful handling of downgrade / unsupported newer schemas.
- **Instruments:** `crash-harness`, `migration-harness`, `test-runner`. Emits `reliability.atomic-write`, `reliability.crash-mid-write`, `reliability.migration-forward`, `reliability.resume-after-reopen`.

---

### 12. `performance-audit` — Real Interactive Performance & Budgets
- **Role:** Canonical Quality Owner.
- **Canonical Rule:** *"No measurement, no recommendation."* Only a measured bottleneck in the product hot path is a defect.
- **What it actually does:**
  - Audits cold start time (time to interactive).
  - Measures resting memory floor (RAM consumed at idle).
  - Evaluates rendering frame budgets (60fps / 16.6ms frame budget during scrolling, editing, animation).
  - Validates install and download footprint against declared limits.
- **Instruments:** `measurement-run`, profiling benchmarks, Lighthouse. Emits `performance.budgets-declared`, `performance.cold-start-ms`, `performance.memory-floor-mb`, `performance.frame-budget-met`.

---

### 13. `design-pro` — UX Heuristics, WCAG 2.2 AA Accessibility & i18n
- **Role:** Canonical Quality Owner.
- **Canonical Rule:** WCAG 2.2 AA with the specific criterion named + Nielsen Norman heuristics on running screens.
- **What it actually does:**
  - Includes 21 specialized domain guidelines covering navigation, forms, error handling, visual hierarchy, search, notifications, settings, onboarding, AI autonomy, etc.
  - Audits accessibility: color contrast, keyboard traversal, focus rings, screen reader DOM landmarks, aria attributes.
  - Audits i18n key completeness across all supported languages.
  - Collects rendered screenshot samples and DOM structures for visual UX review.
- **Instruments:** `screenshot-sample`, `keyboard-traversal`, `dom-inspection`, plus OKLCH candidates from `ui-system`. Emits `a11y-critical-flows`, `ux.heuristic-adherence`, `i18n.key-parity`.

---

### 14. `ui-system` — Design System Architecture, Tokens & Components
- **Role:** Canonical Design System Owner & Toolmaker.
- **Canonical Rule:** OKLCH tokens, 4 elevations, `data-ui` contract — and **never closes an accessibility gate alone**.
- **What it actually does:**
  - Provides a complete design system library: 38 accessible UI components (`accordion`, `button`, `dialog`, `dropdown`, `input`, `table`, etc.).
  - Color themes: `neutral.css`, `studio.css`, `editorial.css`, `heroui.css`, `tailwind-bridge.css`.
  - Executable linter `scripts/audit_ui.py`:
    - Checks boundary isolation (`@project/ui`).
    - Flags legacy/forbidden UI dependencies.
    - Validates OKLCH color lightness delta ($\Delta L$).
    - Verifies focus rings, reduced motion queries, unstyled native tags, and font bundling.
  - Profile applicator `scripts/apply_profile.py` for specialized app domains (e.g. video editor).
- **Instruments:** `audit_ui.py`. Emits `ui.architectural-boundary`, `ui.legacy-package`, `ui.color-mix-sum`, `ui.oklch-delta-l`, `ui.focus-ring`, `ui.reduced-motion`.

---

### 15. `observability` — Production Diagnosability & Telemetry
- **Role:** Canonical Quality Owner.
- **Canonical Rule:** *"A customer says 'doesn'''t work on version X' — what can you find out?"*
- **What it actually does:**
  - Audits structured logging (JSON format, timestamps, standardized severity levels).
  - Traces correlation IDs crossing processes, threads, and network requests.
  - Enforces strict PII redaction (masking tokens, credentials, emails, personal data before logging).
  - Verifies opt-in telemetry and user consent boundaries.
- **Instruments:** `log-inspection`, telemetry verifier. Emits `observability.structured-logs`, `observability.correlation-id-present`, `observability.pii-redacted`, `observability.opt-in-consent`.

---

### 16. `release-audit` — Distribution, Reproducibility & Supply Chain
- **Role:** Canonical Quality Owner.
- **Canonical Rule:** Clean clone $	o$ one command $	o$ the identical artifact.
- **What it actually does:**
  - Audits build determinism: bit-for-bit reproducible packaging.
  - Validates lockfile immutability (`package-lock.json`, `Cargo.lock`).
  - Verifies cryptographic code signing on binaries and installers.
  - Inspects SBOM (Software Bill of Materials) generation and auto-updater signature checking.
- **Instruments:** `reproducibility-run`, binary verifier. Emits `release.reproducible-artifact`, `release.signed-artifact`, `release.sbom-generated`, `release.lockfile-strict`.

---

### 17. `commercial-readiness` — Monetization, Licensing & Legal Compliance
- **Role:** Canonical Quality Owner.
- **Canonical Rule:** Failing and edge commercial paths must be proven, not just the happy path.
- **What it actually does:**
  - Audits the 6 canonical commercial paths (**SELL-01** to **SELL-06**):
    - `SELL-01`: Online & offline activation (air-gapped environments).
    - `SELL-02`: Machine migration and license transfers.
    - `SELL-03`: Trial expiration and trial-to-paid conversions.
    - `SELL-04`: Refund workflows and instant feature revocation.
    - `SELL-05`: Customer support dispatch with declared SLA.
    - `SELL-06`: Subscription cancellation, grace period, and data retention.
  - First-run timing: validates cold launch time on a clean virtual machine.
  - Legal compliance: Third-party codec licenses, GDPR, EU CRA, EAA, and EULA enforcement.
- **Instruments:** `clean-vm-run`, licensing test harness. Emits `sell-01-activation` through `sell-06-end-of-payment`, `commercial.legal-clearance`.

---

### 18. `seo-audit` — Search Engine Optimization & AI Engine Presence
- **Role:** Canonical Quality Owner.
- **Canonical Rule:** Technical SEO + Core Web Vitals + Schema.org + Generative Engine Optimization (GEO/AEO).
- **What it actually does:**
  - Executable engine `scripts/run_seo_audit.mjs` outputs SARIF v2.1.0 findings.
  - Audits technical SEO: HTTP status codes, redirect loops, canonical tags, hreflang, robots.txt, sitemap XML.
  - Audits on-page semantics: title tags, meta descriptions, semantic heading hierarchies (H1–H6), image alt tags.
  - Validates Schema.org JSON-LD structured data.
  - Audits GEO/AEO: readiness for AI crawler discovery (Perplexity, ChatGPT, Google AI Overviews).
- **Instruments:** `run_seo_audit.mjs`, Lighthouse integration. Emits `seo.technical`, `seo.on-page`, `seo.structured-data`, `seo.core-web-vitals`, `seo.geo-aeo`.

---

### 19. `skill-readiness-auditor` — Agent Skill Instruction Quality & Trigger Discriminator
- **Role:** Meta Quality & Readiness Owner.
- **Canonical Rule:** Enforcement of `POLICY.md` standards for AI Agent Skills instruction quality, triggers, workflow coverage, and schema compliance.
- **What it actually does:**
  - Validates YAML frontmatter integrity and schema compliance.
  - Checks description length (< 500 characters to prevent context window saturation).
  - Verifies tool permission patterns (`allowed-tools` / `disallowed-tools`).
  - Verifies empirical claims: directory counts, script paths, and file references must match disk reality.
  - Bilateral pair-check: reciprocal routing between adjacent skills.
  - Anti-prompt-injection validation: review-class skills must declare input as data.
- **Instruments:** `audit.sh`, `test_readiness_audit.py`. Emits `skills.mechanical-lint`, `skills.claims-verified`, `skills.pair-check-valid`.

---

### 20. `skill-security-auditor` — Agent Skill Security, Prompt Injection & Threat Auditor
- **Role:** Meta Security Owner for Agent Skills.
- **Canonical Rule:** Threat modeling, prompt injection resistance, excessive privileges, data exfiltration, supply-chain risks, and Runtime Gate requirements.
- **What it actually does:**
  - Audits for malicious/deceptive instructions, hidden Unicode obfuscation, and prompt injection attempts.
  - Checks for sensitive data access, exfiltration patterns, and lateral skill access.
  - Audits MCP servers and external resource declarations (`external-resources.json`).
  - Integrates with NVIDIA SkillSpector scanner when available.
  - Verifies requirements for Runtime Gate tier assignment (Tier 0 to Tier 3).
- **Instruments:** `security-audit.py`, `skillspector-adapter.py`. Emits `security.scan`, `security.mcp`, `security.runtime-gate-requirement`.

---

### 21. `skill-release-gate` — Agent Skill Release, Signing & Enrolment Authority
- **Role:** Final Gate Decision Authority for Agent Skills.
- **Canonical Rule:** Unified evaluation of readiness and security reports to issue release, signing, or Trust Registry enrolment decisions.
- **What it actually does:**
  - Reads independent evidence from `skill-readiness-auditor` and `skill-security-auditor`.
  - Enforces strict mode requirements for production enrolment.
  - Validates bundle integrity (`bundle-integrity.json`) and provenance/signatures.
  - Issues deterministic decision: `Eligible for enrolment`, `Hold`, `Blocked`, or `Quarantined`.
- **Instruments:** `release-gate.py`. Emits `skills.enrolment-decision`.


## Verify the plugin

Before installing, or after editing it:

```bash
# descriptions under the working ceiling (500 chars)
python3 scripts/measure-descriptions.py .

# zero mechanical findings in readiness
bash skills/skill-readiness-auditor/scripts/audit.sh skills

# validate-report tests
python3 skills/audit-app/scripts/test_validate_report.py

# e2e pipeline test for skills runtime & gate
node --test runtime/tests/e2e-pipeline.test.mjs
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
