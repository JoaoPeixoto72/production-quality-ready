# Video Editor — Quality Standard

Run these checks in addition to the generic `references/quality-standard.md`.

- No font or other runtime asset is loaded from a remote URL.
- Timecodes and numeric values render with tabular figures.
- Accent contrast is reviewed over real video thumbnails, not only plain UI
  surfaces.
- The preview canvas remains pure black.
- Tauri/webview behavior is manually reviewed for overlays, fonts, and focus.
