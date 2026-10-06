---
name: bootstrap-project
description: "Write the project's gates.json and its four adapters (start-work, review-change, close-work, verify) from what the repo already declares. Run once after installing the plugin, and again after a plugin major upgrade. Not for audits. User-invoked only."
allowed-tools: Read Glob Grep Bash Edit Write
---

# bootstrap-project

The plugin is generic. The project is not. This skill closes the gap by
writing the **four adapters that make the generic owners bite on this
codebase** — with the project's real commands, real invariants and real
surfaces — plus the `gates.json` that tells every owner which platform,
sales model and stack they are looking at.

Run it first. Run it again after a plugin major upgrade (it re-reads the
existing adapters and only proposes diffs).

It is the plugin's one **user-invoked** skill (`POLICY.md §2.1`): it writes
into a repo, and a re-run rewrites what a previous run wrote, so the user
names it rather than a model trigger firing it.

## Phase 0 — Detect (never invent)

Read, do not ask, for anything the repo can tell:

| Fact | Source |
|---|---|
| **Host** | `.agents/` exists → `.agents`; `.claude/` exists → `.claude`; both → ask; neither → default `.agents` and say so. |
| **Platform** | `tauri.conf.json`, `electron` dep, `Cargo.toml` with `[[bin]]` → `desktop`. `wrangler.*`, `next.config.*`, `vite.config.*` with SSR, `package.json` with a server framework → `web`. Both → `both`. |
| **Stack** | manifests: `package.json` (+ deps: hono, next, react, vite…), `Cargo.toml`, `pyproject.toml`, `wrangler.jsonc` (d1/r2/kv bindings). |
| **Commands** | `package.json` scripts (`build`, `test`, `typecheck`/`tsc`, `lint`, `dev`), `Cargo.toml` (→ `cargo build --release`, `cargo test`), `Makefile`, `justfile`. |
| **Migrations** | `migrations/*.sql`, `prisma/`, `drizzle/`, `diesel.toml` + any `verify-migrations` script. |
| **Sales model** | `stripe`/`paddle`/`lemonsqueezy` deps → `subscription`; licence-key code / offline activation → `licensed`. Neither → ask. |
| **Surfaces** | routes: `src/routes/**`, `app/**/page.*`, `pages/**`; desktop: window titles in `tauri.conf.json`. |
| **Duplication hotspots** | folders with auth / db / billing / security helpers — candidates for the `start-work` ownership table. |
| **Public URL** | `wrangler.jsonc` routes, `vercel.json`, `CNAME`, README badges. |
| **Existing state doc** | `ESTADO.md`, `STATE.md`, `STATUS.md`, `CLAUDE.md`, `AGENTS.md`. |

Record every detection with its source file. Show the table to the
user before writing anything.

## Phase 1 — Ask only what code cannot tell

1. Human-readable project name.
2. Confirm platform / sales-model / host if detection was ambiguous.
3. **Invariants already paid for** — "we never do X because Y happened".
   Seed the list with what the code reveals (unique indexes, checksum
   scripts, `timingSafeEqual`, tenant guards, idempotency keys) and ask
   the user to confirm the *reason* for each.
4. Test credentials for `verify` (names and where they live — never
   production secrets).
5. **Threat model** — where it lives, or that there is none yet.
   `security-audit` does not run without one; say so now rather than at
   the first audit.
6. Which owners are `not-applicable` and why (e.g. `drive-app-window`
   on web, `audit-website` on desktop). Propose from platform; confirm.
7. **Maintainability budgets** — propose the defaults from
   `../code-review/references/maintainability.md` §1, show what
   `../code-review/scripts/quality_scan.py --format md` finds with them, and let the user set the numbers
   (`owners.code-review.budgets`). Existing debt goes into the baseline
   (`--write-baseline`), never into looser numbers.
8. **Adapter names** — each adapter gets a local name different from
   the plugin skill it extends: `<project>-<skill>` (`<project>-start-work`).
   Two skills with one short name leave the host to pick by chance. Record
   each in `owners.<skill>.adapter`. Adapters are written in English, names
   and body, whatever the project's language (POLICY §3.2).

## Phase 2 — Write

All paths below use `<host>` = `.agents` or `.claude`.

Before writing prose, load `../../rules/writing-for-agents.md`: the pointer
line is the routing, and a body that restates the manifest is a cache that
goes stale.

1. **`<host>/gates.json`** — from `templates/gates.json.template`:
   `platform`, `sales-model`, `stack`, `owners` (applicable +
   `not-applicable` with reason), `adapter-hints` (every detected
   command, including `migrations-verify-command`), `gates`.
2. **`<host>/skills/<local-name>/SKILL.md`** for each of start-work,
   review-change, close-work and verify, from `templates/skills/*.template`
   with every `{{PLACEHOLDER}}` replaced. Pre-fill:
   - `start-work`: ownership table from detected hotspots.
   - `review-change`: platform line, axes that apply, invariants from
     Phase 1, proof commands in order (including `quality_scan.py --since`).
   - `close-work`: document → subject table from the docs that exist.
   - `verify`: launch command, surfaces table, credentials pointer,
     artefact paths (local DB / object store / logs), driver by platform.
3. **`<host>/skills/<local-name>/agents/openai.yaml`** beside each adapter,
   from `templates/skills/openai.local.yaml.template`. Codex reads it for
   the skill picker; without it the adapter still loads, but shows no
   name of its own.
4. **State document** — if none exists, `ESTADO.md` from
   `templates/ESTADO.md.template`; if one exists, do not overwrite —
   propose additions.
5. **Agent map** — if no `AGENTS.md`/`CLAUDE.md` exists, write one from
   `templates/AGENTS.md.template` (named for the host: `AGENTS.md` for
   `.agents`, `CLAUDE.md` for `.claude`). If one exists, propose the
   "code is the source" paragraph (`PURPOSE.md §3.5`) when it lacks one,
   and an "Installed skills" block.
6. **`.gitignore`** — propose `/.work/` (what `map`, `slice`, `research`
   and `spec` write while working) and the audit output (`/.audit/`,
   `/docs/audits/`), so a skill's working files never reach a commit.

## Phase 3 — Verify what was written

1. No `{{…}}` left: `grep -rn "{{" <host>/skills <host>/gates.json`.
2. Every command in `adapter-hints` exists in the manifest it was read
   from.
3. `python <plugin>/scripts/measure-descriptions.py <host>/skills` —
   every adapter description ≤ 250 chars.
4. `pwsh <plugin>/scripts/run-all-owners.ps1 -RepoRoot . -DryRun` lists
   the expected owners for the platform.
5. Every document the adapters reference exists (`ESTADO.md`,
   …). If not, drop the line — never create an empty document or folder
   to satisfy a reference.

Refuse to hand off with any of the five failing. Check 3 matters most
on long project names: the templates leave about 60 characters for them.

## Hard rule: no stored counts

Adapters and the state document store no counts — a count is stale at
the next commit. The state document says pass or fail beside the command:

```
Tests: pass (`npm test`)
```

## Templates

- `templates/gates.json.template`
- `templates/AGENTS.md.template`
- `templates/ESTADO.md.template`
- `templates/skills/start-work.SKILL.md.template`
- `templates/skills/review-change.SKILL.md.template`
- `templates/skills/close-work.SKILL.md.template`
- `templates/skills/verify.local.SKILL.md.template`
- `templates/skills/openai.local.yaml.template`

## Placeholders

| Placeholder | Source |
|---|---|
| `PROJECT_NAME` | Phase 1 |
| `ADAPTER_NAME` | Phase 1 item 8 — one per template |
| `DISPLAY_NAME`, `SHORT_DESCRIPTION` | adapter's human name and one-line summary (Codex picker) |
| `HOST`, `HOST_AGENT_FILE` | Phase 0 (`.agents` → `AGENTS.md`; `.claude` → `CLAUDE.md`) |
| `PLATFORM`, `SALES_MODEL`, `STACK_JSON` | Phase 0 / 1 |
| `AXES_THAT_APPLY` | derived from `PLATFORM` (review-change A1–A11 tags) |
| `BUILD_COMMAND`, `TEST_COMMAND`, `TYPECHECK_COMMAND`, `LINT_COMMAND`, `MIGRATIONS_VERIFY_COMMAND`, `RUN_COMMAND` | Phase 0 |
| `BASE_URL` | dev-command port, or "n/a" |
| `PROJECT_INVARIANTS`, `INVARIANTS_LIST` | Phase 1 (numbered, with reason) |
| `AXES_LOOKUP_TABLE` | Phase 0 — concrete file per axis, or drop the section |
| `PROJECT_SPECIFIC_OWNERSHIP_TABLE` | Phase 0 hotspots |
| `DOCS_NOT_TO_REOPEN` | Phase 0 (the facts and defects documents that exist, and the agent map's closed decisions) |
| `PROJECT_SURFACES_TABLE`, `PROJECT_ARTIFACTS_TABLE`, `TEST_CREDENTIALS`, `PROJECT_TRAPS` | Phase 0 / 1 |
| `VERIFY_DRIVER` | `PLATFORM` (browser automation / `drive-app-window`) |
| `DOC_OWNERSHIP_TABLE` | Phase 0 (docs that exist) |
| `ARCH_DESCRIPTION`, `CONVENTIONS`, `CONTRIBUTION_RULES` | Phase 0 / 1, or drop the section |
| `VERSION`, `HEAD`, `BUILD_STATUS`, `TEST_STATUS`, `TYPECHECK_STATUS` | Phase 3 — the baseline actually run |
| `VERSION_BUMP_RULES` | Phase 1 (or default semver text) |
| `OWNERS_JSON`, `ADAPTER_HINTS_JSON` | Phase 0 / 1 |
| `DATE` | runtime |

## Does not

- Write the project's gate pack beyond the three standard gates.
- Configure CI — `release-audit` reports what is missing.
- Decide licence or price — `commercial-readiness`.
