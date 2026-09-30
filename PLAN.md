# PLAN — plugin `production-quality-ready`

Why the plugin has the shape it has, one entry per version. Nobody reads
this at runtime. The rules live in `PURPOSE.md`, `POLICY.md`,
`CONTRACTS.md` and the skills; what ships is mapped in `README.md`; the
acceptance commands are in `PURPOSE.md §6`. Older rounds (the
refutation rounds, the extraction from `auditar-app`, the English
translation) are in git history — `git log -- PLAN.md`.

---

## Change log

### plugin 3.2.0

**Um instrumento que nunca ficou vermelho não é um gate.** A regra entrou no
contrato (`CONTRACTS §4.6.4`) e, aplicada aos nove instrumentos que o plugin
executa, encontrou quatro defeitos reais no mesmo dia.

1. `secret_scan.py` tinha **dois falsos PASS**: sem git, `git ls-files` devolvia
   zero ficheiros e o veredicto era `PASS` ("não há segredos" a partir de zero
   ficheiros observados); e `.txt` estava na lista de caminhos "fixture", pelo
   que uma chave privada colada num ficheiro de notas era um `PASS` com nota.
   Corrigido: uma varredura vazia é `NOT_VERIFIED`, o `PASS` diz quantos
   ficheiros leu, e `.txt` saiu da lista de fixtures.
2. `threat_model.py` **substitui** o check de existência do runner ("o ficheiro
   existe e um commit tocou-lhe", que um documento vazio satisfazia). Agora o
   threat model tem de citar as provas dos controlos (`caminho:linha`, e o teste
   que as exercita) e cada citação tem de resolver; um modelo sem uma única
   citação falha por isso mesmo (`CONTRACTS §4.6.5`). O primeiro resultado foi
   um **falso positivo do próprio instrumento**: um identificador entre crases
   (`event.id`) contava como citação, e `routes/x.ts` não era resolvido contra a
   raiz do código. Corrigido, o threat model do Provo passa com 43 citações (6
   em testes).
3. `tests/instruments/test_instruments_go_red.py` — 18 testes: um caso-vermelho
   por instrumento (repositório mau, instrumento tem de falhar), mais a regra
   aplicada sozinha (todo o instrumento declarado num `instruments.yaml` tem de
   estar no registo ou ter uma razão escrita para não ter caso-vermelho).
   Instrumentos que são comandos externos, harnesses do projeto ou o próprio
   release têm excepção declarada com a razão, nunca em silêncio.
4. **Defeito registado, não corrigido**: `run_seo_audit.mjs` e
   `run_website_audit.mjs` **abortam** (exit `0xC0000409`) quando o alvo é
   `http://` (servidor local). O motor SEO ainda imprime o veredicto antes de
   morrer; o 360 não imprime nada. Os casos-vermelhos dos dois usam `--dir`
   (hermético, sem rede) e o defeito fica aberto em `PLAN → Open work`.

**Um emparelhamento recuperado (item 1):** `grill` passa a dizer que uma palavra
que um round fixa se escreve no glossário **na mesma sessão**. Era o que o
`grill-with-docs` de outro conjunto garante por chamada de skill; aqui
garante-se por instrução, porque a `POLICY §2.1` mantém que nenhuma skill
invoca outra.

### plugin 3.1.1

**A pair the runner emitted and the owner did not accept.** `run-all-owners.ps1`
writes `web.readiness-clean` from the 360 engine, and
`audit-website/instruments.yaml` did not declare it — an evidence file whose
`(producer, instrument)` pair is not in the owner's manifest, which
`CONTRACTS §4.5` resolves as `NOT_VERIFIED/unauthorized-instrument` and would
have quietly dropped a legitimate PASS. Found by running the runner and
validating the result against the registry, which is what the pair check is
for. The manifest now declares it.

### plugin 3.1.0

**The two owners left over from the comparison, taken deliberately last.**

1. `wizard` — generates the interactive script that walks a person through the
   steps no agent can do: provisioning, dashboard settings, API keys, CI
   secrets. Founding rule: if an agent can run it, it is not a wizard step. The
   secret is read without echo, checked by calling the sandbox, never printed
   back, and the script ends with a pointer to where each value lives — never
   the value. It exists because `ESTADO.md §3` ("waiting on money") is exactly
   this class of blocked work.
2. `improve` — ranks the places a codebase is hard to change into a refactor
   plan a `slice` can execute: shallow modules, missing seams, repeated
   conditionals, pass-through indirection, reachable state. It cites
   `code-review`'s budgets instead of re-declaring them, and its founding rule
   is that a refactor with no proof of no-behaviour-change is a rewrite. It
   closes the gap where debt was measured (M1–M7) and never planned.

Both close no check, so `POLICY §2.4` grew two rows; context cost is now 27
descriptions.

Not taken, and it stays that way: `retro`, `teach`, `to-questionnaire`,
`loop-me`, the writing-* family, host-specific setup skills (`setup-pre-commit`,
`setup-ts-deep-modules`, `git-guardrails`), project-specific migrations
(`migrate-to-shoehorn`), and the five-bucket taxonomy.

### plugin 3.0.0

**Scope, not size: the plugin stops being only a gate and covers idea to
production.** It could audit a codebase well and could not help make one. The
comparison against a skills repository that covers the whole journey produced
nine new owners; each one earns its place by owning a rule the plugin lacked,
not by mirroring a skill.

1. `diagnose` was rewritten from the shallow version shipped in 2.5.0 into the
   discipline it should have been: **Phase 1 is a tight feedback loop** (ten
   ways to construct one; red-capable, deterministic, fast, agent-runnable),
   non-deterministic bugs chased by *raising the reproduction rate*, an
   explicit stop-and-say-so when no loop can be built, redaction before
   anything is shown, three to five **falsifiable hypotheses** ranked and shown
   to the person before testing, one-variable instrumentation, debugger over
   logs, a separate performance branch (baseline, then bisect), the
   **correct-seam** rule (no seam is itself the finding), and a cleanup
   checklist. It also ships `scripts/hitl-loop.template.sh`.
2. `grill` **interrogates a plan**: the design tree worked in rounds, the
   unblocked frontier asked in one round, a recommended answer beside every
   question, the facts found rather than asked for, done when the frontier is
   empty and the person confirms. This is the owner that exists because a plan
   nobody questioned is a plan full of assumptions.
3. `spec` keeps the criteria and gained the interview ("run the loop in
   `grill`") plus `references/glossary-and-adr.md`: one term, one meaning; a
   decision recorded once and never edited.
4. `slice` turns an agreed spec into **tracer-bullet** slices — each cutting
   every layer, verifiable alone, sized to one session, with declared blocking
   edges — and sequences a **wide refactor** as expand–contract. It quizzes the
   person on granularity before publishing.
5. `map` charts work too large for one session: a destination, an index of
   decisions, the **fog** that cannot be phrased yet, what is out of scope, and
   decision tickets of four types (research, prototype, grill, task) — one
   ticket per session, claimed before work.
6. `research` answers a question from **primary sources**, each claim with the
   version it holds for, and leaves the answer as a file in the repo.
7. `prototype` writes throwaway code that answers one design question — a
   logic/state walkthrough or several UI variants on one route — and captures
   the decision, not the demo.
8. `triage` moves incoming issues and external pull requests through two
   category roles and five state roles, **verifies the claim against the code
   before writing any brief**, checks redundancy by concept and the rejected
   record, and leaves a brief an agent can pick up.
9. `handoff` packages work: a pull-request body with Summary, Evidence
   before/after and **Merge Danger** (one-way or two-way door, blast radius),
   or a session handoff file outside the workspace that references artefacts
   instead of copying them.
10. `ship` — the last mile **neither this plugin nor the one it was compared
    with had**: version and changelog, tag, deploy, production smoke, the
    rollback named before the first action, and the deploy log and smoke output
    as the proof. `release-audit` and `verify` accept it as a producer in their
    `instruments.yaml`, so the verdicts stay with their owners.

`ship` is **user-invoked**, like `bootstrap-project`: it acts on production,
and that decision belongs to the person. `POLICY §2.1` now states the rule (an
automatic trigger that can cost more than it saves) and names both.

Taken as rules, not as owners: redaction before showing output, citing the
source of a claim, and re-pitching a message that did not land — they live in
`rules/writing-for-agents.md`. Not taken: tickets-first triage for repos that
receive no issues, `retro`, `teach`, `to-questionnaire`, `loop-me`, the
writing-* family, host-specific setup skills, and the five-bucket taxonomy.

Context cost: 25 skill descriptions, 5 841 characters, against Codex's 8 000
character list budget.

`research` declares `WebFetch`, so it joins `audit-website` as a
network-capable skill whose runtime enforcement belongs to the host. The
security audit reports that gate as unverified, by design: the plugin
cannot attest what the host enforces.

### plugin 2.5.0

**The lifecycle gained its two missing owners, and Codex gained an install
path.** The plugin was a quality gate: it could ask *is it well made?* and
never *is it the right thing?*. Compared against a skills repository that
covers idea to production, only the gaps that were real were closed.

1. `spec` — requirements before code: problem, numbered acceptance criteria
   each with the proof that shows it, invariants touched, out of scope, open
   questions. It exists because `review-change` had nothing to judge intent
   against, and because a criterion nobody can observe is not a criterion.
2. `diagnose` — cause before fix: smallest reproduction with its captured
   log, the assertion that tells right from wrong, narrowing by bisect, the
   invariant that was broken, the fix at the cause, and the regression test
   that fails on the pre-fix commit. It exists because `review-change`
   pointed at a "`start-work` step 5" that does not exist.
3. `review-change` now judges **two axes that are never merged**: Standards
   (built right) and Spec (the right thing), each with its own worst issue
   and no single winner. A project with no spec resolves
   `NOT_VERIFIED/no-spec` instead of inventing requirements; a spec that
   exists with a criterion that has no proof is that axis's first `BLOCKED`.
4. `code-review` gained `references/test-design.md`: the declared risk and
   oracle, the A/B/C grades, oracles that hold and that do not, determinism,
   and mutation as the cheap check. It replaces taking `tdd` as a skill.
5. `scripts/link-skills.ps1` and `scripts/link-skills.sh` make the plugin's
   skills visible to Codex, which reads `.agents/skills` and never
   `.agents/plugins/`. 2.4.0 shipped the Codex metadata without an install
   path; this is that path. `install.ps1 -Codex` / `install.sh --codex` run
   it. Junctions on Windows need no elevation.

Not taken: tickets, triage, wizard, retro, handoff, teach, `tdd` as a skill,
and the five-bucket taxonomy. Each either duplicates an owner already here
(`close-work` owns the state document, `spec` owns the criteria) or pays
permanent context for a verb nobody types.

### plugin 2.4.0

**Two host gaps closed, one rule file added.** Compared, mechanism by
mechanism, against a skills repository that had taken the same ideas further
(distribution, invocation, authoring discipline), and only what removed a
real gap was taken.

1. Codex is a first-class host now: every skill carries `agents/openai.yaml`
   (`interface.display_name`, `interface.short_description`), the file Codex
   reads for its skill picker. The plugin said host-agnostic while only
   Claude Code could show a skill's own name. `bootstrap-project` writes the
   same file beside each adapter it generates, from a new template.
2. `bootstrap-project` is **user-invoked**: `disable-model-invocation: true`,
   plus `policy.allow_implicit_invocation: false` beside it. It writes into
   the repo and a re-run rewrites what an earlier run wrote, so the user
   names it. `POLICY §2.1` no longer states that no skill sets the field; it
   names the one skill and the reason.
3. New `rules/writing-for-agents.md`: the discipline for anything an agent
   reads. The pointer's wording is the routing; inline what every branch
   needs and disclose the rest; say the target, not the ban; a step ends on
   a criterion; delete no-ops and stale caches. `bootstrap-project` and
   `POLICY §3.1` point at it. It exists because the plugin had evidence rules
   and no authoring rules.
4. The anti prompt-injection clause, duplicated across nine owners with only
   the subject list varying, now has one owner:
   `rules/anti-prompt-injection.md`. Each owner keeps a one-line guardrail
   and a pointer. The measured saving is small (~30 characters per skill);
   the win is that the handling changes in one place.
5. Drift introduced by 2.3.2 fixed: `POLICY §6` and `CONTRACTS §6.4` still said
   the version lived only in `.claude-plugin/plugin.json`.

Not taken, and why: changesets plus a release workflow, a docs page per
skill, a symlink installer and a five-bucket taxonomy all pay for a public
38-skill product. This plugin serves two projects, and the version assert in
CI already removes the drift those mechanisms guard against.

### plugin 2.3.2

**The plugin's own gates could not fail, and the installed project had drifted.**

1. `scripts/measure-descriptions.py` printed `OVER-CEILING` and returned 0:
   the ceiling the README and the generator's Phase 3 both promise was never
   enforced. It returns 1 on any over-budget `description` now.
2. The documented acceptance commands were broken:
   `python -m unittest discover -s tests/audit-app` fails, because the
   directories contain a hyphen (`Start directory is not importable`).
   `README` and `PURPOSE §6` now run `python -m pytest tests`; a CI workflow
   (`.github/workflows/verify.yml`) runs the ceiling and the 76 tests, so the
   falsifiable criteria of `PURPOSE §6` are executable.
3. The Provo instance was frozen at 2.0.0 (no bootstrap re-run): its four
   adapters carried `version:`, `extends: …@2.x` and a `contract:` snapshot
   path, and `gates.json` a `plugin-version` — fields the current templates no
   longer emit — and their descriptions were 318–338 chars, over the plugin's
   own 250. Aligned to the current templates **in place**: the project tables,
   invariants and surfaces were kept, not regenerated. The missing re-run/merge
   mode remains the root cause (see Open work).
4. The version was reachable only through `.claude-plugin/plugin.json`, a path
   a non-Claude host does not read: the plugin is host-agnostic but its version
   was not. The root `plugin.json` carries it too now, and `verify.yml` asserts
   the two manifests agree, so the single value cannot drift.

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
version *value*, carried by the host manifests — `.claude-plugin/plugin.json`
for Claude Code and the root `plugin.json` for other hosts — and kept
equal by a CI check (`verify.yml`); a
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

- **Os dois motores de website abortam em alvos `http://`** (exit `0xC0000409`,
  Windows): `run_seo_audit.mjs --url=http://...` imprime o veredicto e morre
  depois; `run_website_audit.mjs --url=http://...` morre sem output. Um
  servidor local é o alvo natural de qualquer verificação antes de um deploy,
  portanto isto fecha-se com um teste de fumo que corra os dois contra um
  `127.0.0.1`. Os casos-vermelhos actuais usam `--dir` e não exercitam o
  caminho de rede.


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
