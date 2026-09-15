---
name: verify
description: "Prove a change in the real app — start it, drive it by actions, take screenshots, compare before/after. Universal contract; each project supplies a local adapter (requires-adapter: true) with paths, .exe and pilot projects. The harness that drives the Win32/WebView2 window is drive-app-window; this skill is the proof strategy, not the mechanism. Use for \"see this change working\", \"prove without relying on tests alone\". Do NOT use for cargo test — that's code-review-runtime."
contract: CONTRACTS.md
evidence-schema: "1.3.x"
requires-adapter: true
adapter-contract: adapter-contracts/verify.md
version: 1.0.0
allowed-tools: Read, Glob, Grep, Bash, Write
disallowed-tools: Edit, MultiEdit, NotebookEdit
---

# verify

**What tests can't catch is in the window.** This skill is the proof
strategy for changes to visible behaviour. Who drives the window is
`drive-app-window` (Windows/Tauri) — this owner decides *what* to prove
and *how to read* what the window returns. Bilateral pair with
`drive-app-window` (POLICY §1.2).

## Founding rule: show, don't describe

A change is verified when there is **an artifact that shows it**: a
before/after image, a structured log of what happened, a file the app
produced with hash compared. Describing the change in prose is intent;
the artifact is proof. No verdict closes without an artifact.

## `requires-adapter: true`

This skill is a **contract**, not an implementation. A project that
activates it must supply the local adapter — see
`adapter-contracts/verify.md` for the full contract. Without an adapter,
the skill returns `NOT_VERIFIED/missing-adapter` (CONTRACTS §4.5). The
adapter provides:

1. Command to launch the app + a check that the binary is newer than
   the sources.
2. Path where the app leaves the artifacts it writes.
3. Project-specific traps that are neither general nor covered by
   `drive-app-window`.
4. Pilot projects — quick examples for smoke tests.

## Canonical order

1. **Launch** — the adapter's command; never wait for a slow build if
   there's already a fresh binary. If sources are newer than the
   binary, run the build first (the adapter says which).
2. **Reach the initial state** — open a pilot project, wait for it to
   settle (the adapter says which signal — status bar, event).
3. **Execute actions** — `drive-app-window` for
   click/type/scroll (Windows) or the platform equivalent.
4. **Capture** — `content` (never `shot` in a WebView2, which comes back
   blank) before and after. Each file named with the step and the HEAD
   hash.
5. **Read what the app wrote** — output files, logs, cache. The adapter
   says where.
6. **Compare** — hashes, text, image. Expected differences listed
   upfront; unexpected differences are findings.
7. **Close the app** — Windows holds the `.exe` while it runs; the next
   build silently fails if the app stays open.

## Where artifacts live

The conventional folder is `.verify/` at the repo root, in `.gitignore`.
It's where session PNGs, logs and diffs go. Never in the tracked repo —
a proof session is intermediate, not history.

## Common traps (project-independent)

- **Blank screenshot in a WebView2.** Not an app bug; `PrintWindow` read
  before the GPU composed. Always use `-Action content` (see
  `drive-app-window`).
- **Invisible secondary window** (Tauri opens a 16x16). Searching by
  `MainWindowHandle` falls on it; always search by title. That is
  `drive-app-window`'s rule; here it's a warning.
- **Font falling to generic sans-serif.** Two very different fonts
  rendering *identical to each other* is the sign that neither loaded.
  Never a "harness rendering problem".
- **Open app blocks the next build.** `taskkill //IM <exe> //F` at
  end of session; otherwise the next `build` fails with a linking
  error that never mentions the app was open.

## Boundaries

- **drive-app-window** — bilateral pair. Here: the *what* and *why* of
  what you're proving. There: the *how* of clicking/capturing.
- **code-review-runtime** — automated tests (`cargo test`, `npm test`).
  Here: what those tests can't prove by themselves.
- **reliability-audit** — persistence and migration. If the change is
  about how the file is written, the adapter cites `reliability-audit`.
- **observability** — if the change alters what the app diagnoses in
  the field, the adapter cites `observability`.

## This owner does NOT

- Drive the window itself — that's `drive-app-window`.
- Run `cargo test` — that's `code-review-runtime`.
- Decide whether a feature is commercially ready — that's
  `commercial-readiness`.

## Accepted instruments

See `instruments.yaml`. Canonical producers:
`drive-app-window::gui.ps1` (Windows harness) + the project's local
adapter (launch commands, artifact reading). Without an adapter,
`NOT_VERIFIED/missing-adapter`.
