---
name: verify
description: "Test a change in the running app: launch it, drive real actions, capture before/after artefacts and compare. Web via browser automation, desktop via drive-app-window. Use for 'see this working'. Not for running the test suite (code-review)."
contract: CONTRACTS.md
platforms: [web, desktop]
requires-adapter: true
adapter-contract: adapter-contracts/verify.md
allowed-tools: Read, Glob, Grep, Bash, Write
disallowed-tools: Edit, MultiEdit, NotebookEdit
---

# verify

**What tests can't catch is on the screen.** This skill decides *what*
to prove and *how to read* what the app returns. The mechanism that
drives the app is a driver chosen by platform:

| Platform | Driver | Capture |
|---|---|---|
| web | browser automation available in the host (`chrome-devtools_*` tools, Playwright, or `curl` for API-only flows) | screenshot, a11y snapshot, DOM, network log, response body |
| desktop | `drive-app-window` (Win32/WebView2/Tauri) | `content` capture, event log, files the app wrote |

Bilateral pair with `drive-app-window` on desktop (POLICY §1.2).

## Founding rule: show, don't describe

A change is verified when there is **an artefact that shows it**: a
before/after image, an a11y snapshot with the new node, a structured
log, a file with its hash compared. Prose is intent; the artefact is
proof. No verdict closes without one.

## `requires-adapter: true`

This skill is a contract. The local adapter supplies:

1. **Launch** — command to start the app (dev server or binary) and how
   to tell the build is fresher than the sources.
2. **Surfaces** — routes / screens / windows worth proving, with what
   each one is for.
3. **Credentials** — test accounts and where secrets come from (never
   the values of production secrets).
4. **Artefact paths** — where the app writes (local DB, object store,
   logs).
5. **Traps** — project-specific pitfalls not covered below.

Without an adapter: `NOT_VERIFIED/missing-adapter`.

## Canonical order

1. **Launch** (adapter command). Rebuild first if sources are newer.
2. **Reach the initial state** — open the route / project; wait for the
   settle signal the adapter names.
3. **Before** — capture.
4. **Act** — drive the user flow with the platform driver. Keyboard-only
   pass when the change touches interactive UI (feeds `design-pro`).
5. **After** — capture; read what the app wrote (DB row, file, log).
6. **Compare** — expected differences listed upfront; unexpected ones
   are findings.
7. **Tear down** — stop the dev server / close the app (an open desktop
   binary silently breaks the next build).

## Where artefacts live

`.verify/` at the repo root, git-ignored. Each file named
`<step>-<HEAD>.{png,json,log}`. Never committed.

## Common traps

**Web**
- A page that "works" with cache: reload with cache disabled before the
  *before* capture.
- SSR vs hydrated: capture both when the change touches first paint.
- Local dev DB differs from production schema: run migrations locally
  first (adapter says how).

**Desktop**
- Blank screenshot in WebView2 → use `content` capture, not `shot`.
- Tauri opens an invisible 16×16 helper window → search by title.
- Two different fonts rendering identically → neither loaded.
- Open `.exe` blocks the next build → `taskkill` at end of session.

## Boundaries

- **drive-app-window** — desktop driver. Here: what and why; there: how.
- **code-review** — automated tests. Here: what they cannot prove alone.
- **design-pro** — closes the a11y verdict from the keyboard pass done here.
- **reliability-audit** — if the change alters how data is written or
  what is logged, the adapter cites it.

## Accepted instruments

See `instruments.yaml`. Producers: `drive-app-window::gui.ps1`
(desktop), `verify::browser-driver` (web — chrome-devtools / Playwright /
curl, recorded as `command:`), and the local adapter. A `PASS` without
`command` and an artefact `log` is invalid (CONTRACTS §4.6).
