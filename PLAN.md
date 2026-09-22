# PLAN — plugin `production-quality-ready`

Log of what was proposed and each correction, with the reason.

**Plan version**: 5.0.0

`PLAN.md` is not read at runtime by anyone. It exists so a future
reviewer can see *why* the current shape looks the way it does. The
authoritative files are `PURPOSE.md`, `POLICY.md`, `CONTRACTS.md`, and
the skills themselves.

---

## 1. Non-negotiable framing

Four decisions inherited from the constitutional round of the
`auditar-app`. Their reopening cost is high enough that each requires
a written argument stronger than the ones that closed them.

- **The plugin is the install unit; the skill is the activation
  unit.** A skill pays context permanently; that is what forces the
  ceiling on how many are allowed to exist. Sub-topics stay as
  references inside their owning skill.
- **One subject, one owner, one rule.** Multiple instruments per rule
  are correct; multiple owners of a rule are the defect the plugin
  was built to eliminate.
- **Evidence is a file, not a call.** `audit-app` reads
  `.audit/**/*.evidence.yaml`; it does not invoke skills, does not
  run commands against the audited repo, and running it twice
  produces the same verdict.
- **A skill that asserts facts about a repository lives in that
  repository's commit.** The plugin is agnostic; what knows about the
  project is the local adapter.

---

## 2. What the plugin ships

Skills grouped by role are listed in `PURPOSE.md §2`. The universal
policy is in `POLICY.md`; the mechanical contract is in
`CONTRACTS.md`.

The plugin ships:

- `PURPOSE.md`, `POLICY.md`, `CONTRACTS.md`, `README.md`, and this
  `PLAN.md`.
- `skills/*/SKILL.md` with `description` under the working ceiling,
  each with `instruments.yaml` where applicable.
- `adapter-contracts/*.md` for the four skills that require a local
  adapter (`start-work`, `review-change`, `close-work`, `verify`).
- `scripts/measure-descriptions.py` as the single source of truth for
  `description` counts (exit 1 above 250 chars).
- `scripts/run-all-owners.ps1` — runs what the plugin can run, writes
  evidence with `command:` + `log:`, declares the rest as
  `NOT_VERIFIED/missing-instrument`.
- `skills/audit-app/scripts/validate_evidence.py` — mechanical check of
  every `.audit/**/*.evidence.yaml` against CONTRACTS §3.1/§3.5/§4.5/§4.6.
- Templates under `skills/bootstrap-project/templates/` for a fresh
  repo (gates.json, AGENTS.md, ESTADO.md, four adapters).

---

## 3. Acceptance

Criteria are stated in `PURPOSE.md §6` with the exact commands. Every
release runs them. No count is repeated in prose in this file — see
that section.

---

## 4. Change log

Kept **short** on purpose. Details of each phase live in the version
appendices of `POLICY.md` and `CONTRACTS.md`, closer to the rules
they changed.

### v5.0.0 (current) — plugin v2.0.0

**Audit of the plugin against a real project (Provo, Cloudflare
Workers + Hono + D1) found four structural defects; this version
closes them.**

1. **Fabricated evidence.** 30 of 43 `.audit/**` files in the pilot
   project said `result: PASS / confidence: OBSERVED` with no command
   and no log — written by the model after reading source.
   `run-all-owners.ps1` also registered a `Passed 1` for an owner it
   never executed and templated ten `ui-system` checks without parsing
   the instrument's output. **Fix:** CONTRACTS §3.1.5/§4.6 — `PASS`
   requires `command:` + `log:` on disk; `validate_evidence.py`
   downgrades the rest to `NOT_VERIFIED/no-log`; the runner's
   `Write-Evidence` throws if asked to write a PASS without a trace
   and now parses `audit_ui.py` JSON into per-check verdicts.
2. **Not agnostic.** Desktop-only assumptions (installer signing,
   offline activation, `kill -9` harness, Win32 window) sat beside
   web-only ones (SEO, cookies) with no way to tell which applied.
   **Fix:** `platforms:` on every owner and instrument; `platform:` and
   `sales-model:` in `gates.json`; checks for the other platform
   resolve `NOT_APPLICABLE/platform` automatically. Owners that had
   only one platform in mind gained the other (`release-audit`:
   deploy/rollback; `reliability-audit`: managed-DB atomicity;
   `commercial-readiness`: subscription rows; `security-audit`:
   `sec.tenant-isolation`; `verify`: browser driver).
3. **Duplication and dead weight.** 22 skills where 14 do the work:
   two near-identical SEO engines, contract checks produced by the
   runtime owner anyway, a desktop-centric performance owner whose web
   half lived in SEO, 12 generic "how to be an agent" files inside
   `design-pro`, 39 React components shipped to a `hono/jsx` project,
   three skill meta-auditors (484 kB) that audit skills rather than
   products, historical migration notes and a JustClip gate template.
   **Fix:** `code-review-runtime` + `code-review-contract` +
   `performance-audit` → `code-review`; `observability` →
   `reliability-audit` §2; `seo-audit` → `audit-website/seo/`;
   `design-pro/agent/` 12 → 3 files; React components → optional
   `ui-system/packs/react-components/` (`apply_profile.py --with-react`);
   meta-auditors moved out of the plugin; migration/legacy files deleted.
4. **Context cost and host lock-in.** 9 466 description chars in the
   plugin alone (Claude Code drops skills silently above 15 000 total);
   every SKILL.md hardcoded `.claude/` while the pilot host used
   `.agents/`. **Fix:** all descriptions ≤ 250 chars, directive, third
   person (3 661 total, −61 %); `measure-descriptions.py` exits 1 above
   the ceiling; every path is `<host>/…` with `.agents` and `.claude`
   both detected by `audit-app`, `run-all-owners.ps1`,
   `validate_evidence.py` and `bootstrap-project`.

`bootstrap-project` is now declared the first skill to run: it detects
host, stack, platform and commands, asks only what code cannot tell,
and writes the four adapters **pre-filled** — the per-project layer
the pilot showed to be where all the value lives.

### v4.0.0

**Full translation into English.** The plugin was originally written
in Portuguese; every top-level document, every `SKILL.md` body, every
template, every adapter-contract file, and the four work-cycle
template names were translated. No semantic change; no field renamed;
no rule modified. `evidence-schema: 1.3.x` unchanged.

**Rationale.** The plugin's interface — descriptions, cross-references,
routing verbs — is read by AI agents. Mixing languages inside those
strings makes discrimination worse; consistency across the whole
plugin is worth more than the historical patina of writing it in the
author's first language. English also matches the standards it cites
(WCAG, ASVS, HIG) and the common language of the tools it integrates
with.

**Also in v4.0.0**: numeric assertions removed from prose across
`PURPOSE.md`, `POLICY.md`, `PLAN.md`, `README.md`. Every count is now
one of two things: a named list (the pairs table in `POLICY §1.2`, the
subject table in `PURPOSE §4`, the canonical registry in
`CONTRACTS §7.4`) that a machine can traverse and a human can read, or
a command in `PURPOSE §6` that regenerates the number on demand. The
old cadence of "13 pairs / 14 pairs / recounting" was itself a symptom
of hardcoding counts that change every release.

### v3.2.0

Pair-check recount after the audit-owner bodies were written. Four
defects: the work-cycle triangle not declared, `audit-app ↔
review-change` missing, `code-review-runtime ↔ verify` missing, and
`validate_report.py` importing a `validate_skill.py` that lived only
in the original `auditar-app` repo. All four closed.

### v3.1.0

Three work-cycle skills written (`start-work`, `review-change`,
`close-work`) and their adapter-contracts added. `bootstrap-project`
templates ceased to carry unfilled `{{DESCRIPTION_*}}` placeholders;
`CONTRACT_PATH` resolution declared (absolute-path or snapshot).

### v3.0.0

Fases 2–7 concluded. Motor extracted from `auditar-app` into
`audit-app`. Six existing skills refactored with `instruments.yaml`;
four new audit owners written (`observability`, `release-audit`,
`commercial-readiness`, `performance-audit`). `bootstrap-project`
skill authored with four templates. `skill-readiness-auditor` self-run: zero
mechanical findings.

### v2.0.0

Engine extraction. `auditar-app/references/contrato-e-evidencia.md`,
`auditar-app/references/relatorio.md`, and the validation scripts
moved from the JustClip repo into the plugin's `audit-app` folder.

### v1.x

Adversarial-refutation rounds against the original design. Each round
uncovered defects registered in the version appendices of
`POLICY.md` and `CONTRACTS.md`. Salient ones:

- **First refutation** — `producer`/`instrument` split added to
  evidence schema (`CONTRACTS §3.1`), because "who owns the rule" and
  "who ran the instrument" had been conflated as one field.
- **Second refutation** — silent-PASS defect fixed: an owner missing
  from `gates.json` was silently ignored. Now: explicit
  non-applicability with a reason, or the file itself is a defect.
- **Third refutation** — mechanical authority chain formalized
  (`CONTRACTS §4.5`) with `instruments.yaml` per owner.
- **Fourth refutation** — canonicals-fallback removed from
  `coverage-complete`; strict read-only established (`CONTRACTS
  §7.5`); preconditions renamed `adapter-hints:` and marked as
  never-read by the orchestrator.
- **Sixth refutation** — the work-cycle triangle discovered as a
  missing pair set; four `bootstrap-project` templates fixed to carry
  real descriptions.
- **Seventh refutation** — the pair-check exposed a mismatch between
  `audit-app`'s description and `review-change`'s, and between
  `code-review-runtime`'s and `verify`'s. Both fixed cirurgically.

The complete series is not reproduced here — the round-by-round
reasoning is preserved in git history of the earlier plan revisions
(v1.0.0 through v3.2.0). The current v4.0.0 keeps the outcome and
sheds the archaeology.

---

## 5. Open work

One item, and no file inside the plugin can close it:

**Run `audit-app` against a real project and cross-check its verdict
with a hand-made audit of the same commit.** That is the gate that
separates "the plugin is coherent" from "the plugin is right".
Recorded in `PURPOSE.md §8`.

Every other item on the roadmap is a possible extension, not a
missing piece:

- `bootstrap-project` re-run mode that diffs existing adapters
  (`POLICY §6.4`).
- More instruments the runner can execute without a project harness
  (Lighthouse via headless Chrome for `web.core-web-vitals`, `cargo
  deny` for `sec.deps-provenance`, two-build hash compare for
  `release.reproducible-artifact`).
- Additional profile packs for `ui-system` and `audit-website/seo`
  as new project shapes appear.
- Cross-plugin evidence federation (multiple plugins writing under
  the same `.audit/` root) — not on any roadmap yet, listed as a
  known future stress point.
