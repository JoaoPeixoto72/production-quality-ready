# first-run — commercial-readiness

Ruler for the `first-run-timed` check.

## Protocol

1. **Clean VM.** A fresh Windows/Mac with nothing beyond what the app assumes
   exists (e.g. WebView2 on older Windows 10).
2. **No network for part of the test.** Start without internet — the app must
   not hang waiting for an external server.
3. **Stopwatch.** From double-clicking the installer to the first useful result
   (not the first pixel — the first moment the user can do what they came for).

## Record

- Time (seconds).
- What the app downloaded meanwhile (binaries, models).
- Which permissions it asked for, and in what order.
- Whether it asked for licence confirmation before being useful (activation
  friction vs value).

## Ruler

- Installer → first useful result in < 5 min: `PASS`.
- 5–15 min: `MEDIUM`.
- > 15 min or "could not" (network dropped, download failed, permission denied
  midway with no recovery): `FAIL`.
