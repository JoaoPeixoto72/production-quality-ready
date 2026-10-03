# code-review — Rust + Frontend (Tauri, Electron-like)

Ruler for projects with a Rust backend and a web frontend (Tauri is the
default case). Read `rust.md` and `frontend.md` first: this file covers **only**
what the combination adds inside each layer — the boundary itself (invoke,
events, IPC permissions) is this owner's *Contract* section.

## Rust side

- `#[tauri::command]` commands are a boundary (*Contract*). Here: whether the
  command's *body* copes with already-validated input.
- `AppHandle`/`Window`/`State<'_, T>` passed to threads: `T: Send + Sync`.
- A panic in a command does not crash the app (Tauri isolates it) but sends a
  generic error to the client — log before letting it propagate.

## Frontend side

- `invoke(...)` returns a `Promise` — treat it like any cancellable call
  (`frontend.md`, "Cancellation").
- Events from Rust (`listen(...)`) need `unlisten()` in the effect's cleanup.
- Never assume the backend is ready on first render: wait for
  `tauri://ready` or the first successful `invoke`.

## Tauri bundle

- The bundle holds the web runtime plus the Rust binary; the budget is about
  the final installer (`perf.bundle-within-budget`).
- Static assets: `tauri.conf.json → build.distDir`; nothing outside that folder
  reaches the product.
