# Video Editor profile

Activate this profile only when the repository is the Tauri video-editor
product or a shared package built specifically for it.

When `ui.config.json` declares:

```json
{
  "profile": "video-editor",
  "platform": "tauri",
  "offline": true
}
```

read these files in addition to the generic core references:

- `profiles/video-editor/references/design-language.md`
- `profiles/video-editor/references/quality-standard.md`
- `profiles/video-editor/references/upstream.md`

Then use the profile CSS entry points under `profiles/video-editor/assets/css/`.
