---
name: bootstrap-project
description: "Generate the files a new repo needs to consume the production-quality-ready plugin — CLAUDE.md, ESTADO.md, .claude/gates.json (from the audit-app template), and 4 local adapter skills (start-work, review-change, close-work, verify) that cite the plugin's owners. Every number generated carries the command that produced it. Use on a fresh repo. Do NOT use to migrate a repo already on auditar-app 2.3.x — see audit-app/migration/from-auditar-app-2.3.md."
contract: CONTRACTS.md
evidence-schema: "1.3.x"
version: 1.0.0
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---

# bootstrap-project

Generate the skeleton a fresh repo needs to consume the production-quality-ready
plugin.

## Flow

1. **Read the repo — never invent.** Real package manager, manifest files,
   tooling, project type. Phase 0 of `audit-app` reused.
2. **Ask what can't be derived from code:**
   - Human-readable project name.
   - Branching rule (main-only, gitflow, trunk-based).
   - Where the release goes (store, direct download, in-app updater).
   - Invariants already paid for once ("we never do X because…").
   - Whether the product sells: `commercial-readiness` applicable or not.
3. **Write `CLAUDE.md`** — map, commands, invariants, conventions,
   boundaries, skills, contribution rules.
4. **Write `ESTADO.md`** — current version, what compiles and passes,
   next step. Empty for the user to fill in.
5. **Write `.claude/gates.json`** from
   `production-quality-ready/skills/audit-app/migration/justclip.gates.json.template`,
   with applicable owners marked and inapplicable ones with
   `not-applicable: "<reason>"` (declared scope, POLICY §5.1.1).
5b. **Resolve CONTRACT_PATH.** Two options, decided in this order:
   - If `production-quality-ready/CONTRACTS.md` is reachable by the agent at an
     absolute path (plugin installed globally in the environment), use
     that path. No duplication.
   - Otherwise, **copy** `production-quality-ready/CONTRACTS.md` to
     `<repo>/.claude/CONTRACTS.md.snapshot` and use
     `../CONTRACTS.md.snapshot` as CONTRACT_PATH. The file carries a
     header: "Snapshot of production-quality-ready vX.Y.Z at <date>. Don't edit
     here; edit in the plugin and re-bootstrap."
6. **Write 4 local adapter skills:**
   - `start-work` — cites plugin `start-work` as base.
   - `review-change` — cites plugin `review-change`.
   - `close-work` — cites plugin `close-work`.
   - `verify` — adapter of universal `verify`, with the project's paths,
     `.exe` and harness specifics. Uses
     `extends: production-quality-ready::verify@1.x`.
7. **Run `skill-auditor --depth deep`** over what was just written.
   Refuse to hand off with an open Blocker.

## Hard rule: every number carries its command

Every number the generator emits carries the command that produced it, in
the final file itself. Format:

```
Tests: 512 (cargo test @ HEAD abc1234, 2026-09-14)
Bundle: 1.8 MB (npm run build @ HEAD abc1234, 2026-09-14)
```

Without this, the defect that bit the original `start-work` returns
(hardcoded test count, ten commits behind the tree).

## Does not

- Not migrate `auditar-app` 2.3.x — see
  `audit-app/migration/from-auditar-app-2.3.md`.
- Not write the project-specific gate pack (which grows as invariants
  are discovered).
- Not configure CI — that's `release-audit` on the first pass.
- Not decide licence or price model — that's `commercial-readiness`.

## Templates

- `templates/CLAUDE.md.template`
- `templates/ESTADO.md.template`
- `templates/skills/start-work.SKILL.md.template`
- `templates/skills/review-change.SKILL.md.template`
- `templates/skills/close-work.SKILL.md.template`
- `templates/skills/verify.local.SKILL.md.template`

## Placeholders replaced by the bootstrap

Each template uses `{{NAME}}` for values that step 2 ("ask what can't be
derived from code") or step 5b ("resolve CONTRACT_PATH") produced:

| Placeholder | Source | Notes |
|---|---|---|
| `PROJECT_NAME` | step 2 (readable name) | used in every template |
| `CONTRACT_PATH` | step 5b | `../CONTRACTS.md.snapshot` (variant B) or absolute path (variant A) |
| `BUILD_COMMAND` | step 1 (read from repo) | e.g. `cargo build --release` |
| `TEST_COMMAND` | step 1 (read from repo) | e.g. `cargo test` |
| `RUN_COMMAND` | step 2 | command to start the app; `verify.local` |
| `DATA_DIR` | step 2 | where the app leaves artifacts; `verify.local` |
| `PROJECT_INVARIANTS` | step 2 (invariants already paid) | `review-change`, `close-work` |
| `PROJECT_SPECIFIC_OWNERSHIP_TABLE` | step 2 + structure | `start-work`; places where code tends to repeat |
| `PROJECT_ARTIFACTS_TABLE` | step 2 | `verify.local`; artifact → path table |
| `DOC_OWNERSHIP_TABLE` | step 3 (CLAUDE/ESTADO files) | `close-work`; document → subject table |
| `VERSION_BUMP_RULES` | step 2 | `close-work`; when to bump version |

Step 7 (`skill-auditor --depth deep`) refuses any SKILL.md with
unreplaced `{{…}}` placeholders.
