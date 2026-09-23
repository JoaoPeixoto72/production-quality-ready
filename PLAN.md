# PLAN — plugin `production-quality-ready`

Why the plugin has the shape it has, one entry per version. Nobody reads
this at runtime. The rules live in `PURPOSE.md`, `POLICY.md`,
`CONTRACTS.md` and the skills; what ships is mapped in `README.md`; the
acceptance commands are in `PURPOSE.md §6`. Older rounds (the
refutation rounds, the extraction from `auditar-app`, the English
translation) are in git history — `git log -- PLAN.md`.

---

## Change log

### plugin 2.3.0

Audited by `skill-auditor` with NVIDIA SkillSpector installed. Three fixes:
`quality_scan.py --since` passed its ref to `git diff` unguarded, so
`--since=--output=<file>` made git write a file — now `--end-of-options`,
with a regression test; tests moved out of the skill bundles to `tests/`
(a skill ships what it runs, and the scanner read the test suite as the
skill's own capabilities); ten long references gained a contents list.
The one scanner finding left on `code-review` is the `git` subprocess
itself — expected, and an operator's risk acceptance, not a code change.

### plugin 2.2.0

**Files are referred to by name, never by version.** Every version
number next to a file — per-skill `version:`, `evidence-schema`,
`extends: …@2.x`, `plugin-version` in `gates.json`, the contract's own
version, the `CONTRACTS.md.snapshot` copy in each project — was a second
statement of a fact the file already makes, and each one had drifted
(2.1.0 found skills saying `1.3.x` under a `2.0.0` contract). Now: one
version, in `.claude-plugin/plugin.json`, because the host reads it; a
report names its contract by SHA-256 (`validate_report.py --contrato`);
a missing field resolves by the reason that names it (`CONTRACTS §6`).
`rule-version` stays — it names an external standard, where the number
is the rule.

**Maintainability gets an owner.** `PURPOSE §4` had no row for "can the
next person change this code", so nobody looked. `code-review` owns it
now: budgets (file, function, nesting, params) declared by the project,
measured by `scripts/quality_scan.py` with a committed baseline as a
ratchet, and the M axes in `review-change` for what no number sees
(`references/maintainability.md`, distilled from Anthropic's
`code-review` and `pr-review-toolkit`, Cursor's thermo-nuclear review
and `addyosmani/agent-skills`). First run on a real Tauri + React repo:
one file over 1000 lines, 198 functions over 50, 15 over nesting 3.

### plugin 2.1.0

**Review of every skill against its own contract.** Six defects where a
skill could not do what the contract asks of it, and a trim of the
documents that told the same thing twice.

1. **Owners that could not write their own evidence.** `design-pro`
   had `Read, Glob, Grep` only — no `Bash` to run a keyboard pass, no
   `Write` for `.audit/`, so every a11y check was `NOT_VERIFIED` by
   construction. `ui-system` has create/migrate/extend modes but
   forbade `Edit`. Both fixed in `allowed-tools`.
2. **Generator failed its own gate.** The four adapter templates carried
   descriptions of 310–320 chars; `bootstrap-project` Phase 3 refuses
   anything over 250. Templates shortened; adapters now get a local name
   distinct from the plugin skill (`POLICY §3.2`).
3. **Promises no file keeps.** `security-audit` said `bootstrap-project`
   asks for the threat model (it didn't — now it does) and that
   `audit-app` re-reads waivers (it doesn't — the owner does, when it
   emits). `release-audit` cited a check id that doesn't exist.
4. **`evidence-schema` vs contract version.** Skills said `1.3.x`,
   the contract said `2.0.0`, and §6.1 said they were the same number.
   They are not: §6.1 now separates the file format from the document,
   and Rule 6.1.1 says a degrade-only rule (PASS needs a trace) applies
   to every schema version.
5. **Trigger collision.** `code-review` and `review-change` both said
   "review a diff". `code-review` is the repo-wide evidence producer;
   the diff before commit is `review-change`.
6. **Rationalisations.** The work cycle gained a short table each of the
   excuses an agent uses to skip a step, with the answer — the one idea
   from `addyosmani/agent-skills` that the cycle lacked. Its planning,
   debugging and "doubt" skills were not imported: the host already
   plans, and the two useful lines (reproduce before fixing; argue
   against your own approval) fit inside `start-work` and
   `review-change`.

Also: version appendices removed from `POLICY.md` and `CONTRACTS.md`
(history is owned here and by git); `PLAN.md` itself cut to this log;
the anti-injection blocks shortened to one form.

### plugin 2.0.0

**Audit of the plugin against a real project (Provo, Cloudflare
Workers + Hono + D1) found four structural defects.**

1. **Fabricated evidence.** 30 of 43 `.audit/**` files said
   `PASS / OBSERVED` with no command and no log — written by the model
   after reading source. **Fix:** `PASS` requires `command:` + `log:` on
   disk (`CONTRACTS §4.6`); `validate_evidence.py` downgrades the rest;
   `run-all-owners.ps1` refuses to write a PASS without a trace.
2. **Not agnostic.** Desktop-only and web-only assumptions sat side by
   side. **Fix:** `platforms:` on every owner and instrument; `platform:`
   and `sales-model:` in `gates.json`; checks for the other platform
   resolve `NOT_APPLICABLE/platform`.
3. **Duplication and dead weight.** 22 skills where 14 did the work.
   **Fix:** runtime + contract + performance → `code-review`;
   `observability` → `reliability-audit §2`; `seo-audit` →
   `audit-website/seo/`; React components → optional pack; the three
   skill meta-auditors moved out (they audit skills, not products).
4. **Context cost and host lock-in.** 9 466 description chars; every
   path hardcoded `.claude/`. **Fix:** descriptions ≤ 250 chars
   (`measure-descriptions.py` exits 1 above); paths are `<host>/…`.

`bootstrap-project` became the first skill to run: the pilot showed the
per-project adapters are where the value lives.

---

## Open work

**Run `audit-app` against a real project and cross-check its verdict
with a hand-made audit of the same commit** (`PURPOSE.md §8`).

Extensions, not missing pieces:

- `audit-app` speaks two vocabularies: `CONTRACTS` (`PASS`/`FAIL`/
  `NOT_VERIFIED`) and its report format (`PROVEN`/`CLEARED`/`UNPROVEN`,
  in `references/relatorio.md` and `validate_report.py`). The mapping is
  declared in `references/contrato-e-evidencia.md`; collapsing to one
  vocabulary needs the validator and its fixtures moved together.
- `bootstrap-project` re-run mode that diffs existing adapters
  (`POLICY §6.4`).
- More instruments the runner can execute without a project harness
  (Lighthouse for `web.core-web-vitals`, `cargo deny` for
  `sec.deps-provenance`, two-build hash compare for
  `release.reproducible-artifact`).
