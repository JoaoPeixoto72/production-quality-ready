# PLAN — plugin `production-quality-ready`

Log of what was proposed and each correction, with the reason.

**Plan version**: 4.0.0

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
  `description` counts.
- Templates under `skills/bootstrap-project/templates/` for a fresh
  repo.

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

### v4.0.0 (current)

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
skill authored with four templates. `skill-auditor` self-run: zero
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

- `bootstrap-project --migrate <from-version>` mode, mentioned in
  `POLICY §6.4`.
- Additional profile packs for `ui-system` (`profiles/*`) and
  `seo-audit` (`profiles/*`) as new project shapes appear.
- Cross-plugin evidence federation (multiple plugins writing under
  the same `.audit/` root) — not on any roadmap yet, listed as a
  known future stress point.
