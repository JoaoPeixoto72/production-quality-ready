# PLAN — plugin `production-quality-ready`

Why the plugin has the shape it has, one entry per version. Nobody reads
this at runtime. The rules live in `PURPOSE.md`, `POLICY.md`,
`CONTRACTS.md` and the skills; what ships is mapped in `README.md`; the
acceptance commands are in `PURPOSE.md §6`. Older rounds (v1.x–v4.0.0:
the refutation rounds, the extraction from `auditar-app`, the English
translation) are in git history — `git log -- PLAN.md`.

---

## Change log

### v6.0.0 — plugin v2.1.0

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

### v5.0.0 — plugin v2.0.0

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
