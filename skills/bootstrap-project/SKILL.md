---
name: bootstrap-project
description: "Run first after installing the plugin: detect host, stack and platform, ask only what code cannot tell, write gates.json and the 4 project adapters (start-work, review-change, close-work, verify). Use on a repo without gates.json. Not for audits."
contract: CONTRACTS.md
evidence-schema: "1.3.x"
platforms: [web, desktop]
version: 2.1.0
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---

# bootstrap-project

The plugin is generic. The project is not. This skill closes the gap by
writing the **four adapters that make the generic owners bite on this
codebase** — with the project's real commands, real invariants and real
surfaces — plus the `gates.json` that tells every owner which platform,
sales model and stack they are looking at.

Run it first. Run it again after a plugin major upgrade (it re-reads the
existing adapters and only proposes diffs).

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
7. **Adapter names** — each adapter gets a local name different from
   the plugin skill it extends (`<project>-start-work`, or a verb in the
   project's language). Two skills with one short name leave the host to
   pick by chance. Record each in `owners.<skill>.adapter`.

## Phase 2 — Write

All paths below use `<host>` = `.agents` or `.claude`.

1. **`<host>/gates.json`** — from `templates/gates.json.template`:
   `platform`, `sales-model`, `stack`, `owners` (applicable +
   `not-applicable` with reason), `adapter-hints` (every detected
   command, including `migrations-verify-command`), `gates`.
2. **`<host>/CONTRACTS.md.snapshot`** — copy of the plugin's
   `CONTRACTS.md` with a header "Snapshot of production-quality-ready
   vX.Y.Z at <date>. Do not edit; edit the plugin and re-bootstrap."
   Adapters reference it as `../CONTRACTS.md.snapshot`.
3. **`<host>/skills/<local-name>/SKILL.md`** for each of start-work,
   review-change, close-work and verify, from `templates/skills/*.template`
   with every `{{PLACEHOLDER}}` replaced. Pre-fill:
   - `start-work`: ownership table from detected hotspots.
   - `review-change`: platform line, axes that apply, invariants from
     Phase 1, proof commands in order.
   - `close-work`: document → subject table from the docs that exist.
   - `verify`: launch command, surfaces table, credentials pointer,
     artefact paths (local DB / object store / logs), driver by platform.
4. **State document** — if none exists, `ESTADO.md` from
   `templates/ESTADO.md.template`; if one exists, do not overwrite —
   propose additions.
5. **Agent map** — if no `AGENTS.md`/`CLAUDE.md` exists, write one from
   `templates/AGENTS.md.template` (named for the host: `AGENTS.md` for
   `.agents`, `CLAUDE.md` for `.claude`). If one exists, only propose a
   "Installed skills" block.

## Phase 3 — Verify what was written

1. No `{{…}}` left: `grep -rn "{{" <host>/skills <host>/gates.json`.
2. Every command in `adapter-hints` exists in the manifest it was read
   from.
3. `python <plugin>/scripts/measure-descriptions.py <host>/skills` —
   every adapter description ≤ 250 chars.
4. `pwsh <plugin>/scripts/run-all-owners.ps1 -RepoRoot . -DryRun` lists
   the expected owners for the platform.
5. Every document the adapters reference exists (`ESTADO.md`,
   `docs/decisoes/`, …). If not, create the folder or drop the line.

Refuse to hand off with any of the five failing. Check 3 matters most
on long project names: the templates leave about 60 characters for them.

## Hard rule: no number without its command

Adapters do not store counts. Counts live in the state document with
the command and HEAD that produced them:

```
Tests: 271 asserts (npm test @ HEAD 2d95870, 2026-09-21)
```

## Templates

- `templates/gates.json.template`
- `templates/AGENTS.md.template`
- `templates/ESTADO.md.template`
- `templates/skills/start-work.SKILL.md.template`
- `templates/skills/review-change.SKILL.md.template`
- `templates/skills/close-work.SKILL.md.template`
- `templates/skills/verify.local.SKILL.md.template`

## Placeholders

| Placeholder | Source |
|---|---|
| `PROJECT_NAME` | Phase 1 |
| `ADAPTER_NAME` | Phase 1 item 7 — one per template |
| `HOST`, `HOST_AGENT_FILE` | Phase 0 (`.agents` → `AGENTS.md`; `.claude` → `CLAUDE.md`) |
| `PLATFORM`, `SALES_MODEL`, `STACK_JSON` | Phase 0 / 1 |
| `AXES_THAT_APPLY` | derived from `PLATFORM` (review-change A1–A11 tags) |
| `CONTRACT_PATH` | `../CONTRACTS.md.snapshot` |
| `BUILD_COMMAND`, `TEST_COMMAND`, `TYPECHECK_COMMAND`, `LINT_COMMAND`, `MIGRATIONS_VERIFY_COMMAND`, `RUN_COMMAND` | Phase 0 |
| `BASE_URL` | dev-command port, or "n/a" |
| `PROJECT_INVARIANTS`, `INVARIANTS_LIST` | Phase 1 (numbered, with reason) |
| `AXES_LOOKUP_TABLE` | Phase 0 — concrete file per axis, or drop the section |
| `PROJECT_SPECIFIC_OWNERSHIP_TABLE` | Phase 0 hotspots |
| `DOCS_NOT_TO_REOPEN` | Phase 0 (decision / fact / audit docs that exist) |
| `PROJECT_SURFACES_TABLE`, `PROJECT_ARTIFACTS_TABLE`, `TEST_CREDENTIALS`, `PROJECT_TRAPS` | Phase 0 / 1 |
| `VERIFY_DRIVER` | `PLATFORM` (browser automation / `drive-app-window`) |
| `DOC_OWNERSHIP_TABLE` | Phase 0 (docs that exist) |
| `ARCH_DESCRIPTION`, `CONVENTIONS`, `CONTRIBUTION_RULES` | Phase 0 / 1, or drop the section |
| `VERSION`, `HEAD`, `BUILD_STATUS`, `TEST_STATUS`, `TYPECHECK_STATUS` | Phase 3 — the baseline actually run |
| `VERSION_BUMP_RULES` | Phase 1 (or default semver text) |
| `OWNERS_JSON`, `ADAPTER_HINTS_JSON` | Phase 0 / 1 |
| `DATE`, `PLUGIN_VERSION` | runtime |

## Does not

- Write the project's gate pack beyond the three standard gates.
- Configure CI — `release-audit` reports what is missing.
- Decide licence or price — `commercial-readiness`.
