# Utility Features

Utility features keep power users loyal. They cut repetitive work and let users shape the app to their habits.

## Checklist

| Item | Guidance |
|---|---|
| Favorites / bookmarks | Save icon on content cards. Saved list one tap from main nav. |
| Native share sheet | Uses the platform share sheet. Never a custom UI. Includes a shareable URL. |
| In-app browser + escape | External links may open in-app but always with a visible "Open in browser" action. |
| Personalization | User chooses interests, layout, or notification frequency, starting at onboarding. |
| Clipboard-safe detection | Uses platform APIs that don't trigger paste-prompt for detection. |

## Patterns

- **Share sheet.** Pre-populate a useful message, not a bare URL. Include UTM parameters where you track.
- **Favorites architecture.** Save locally first, sync in background. Never silent failures. Fill-animation confirms save. Empty state invites the first save.
- **Personalization.** Start with an explicit onboarding step. Refine over time with behavior. Always show "Why am I seeing this?" for recommendations (see `./ai-automation.md`).
- **Clipboard.** iOS 16+: use `UIPasteboard.detectPatterns` to detect a URL without reading contents. Android 12+: system toast on any read — only read at the moment of use. Show a subtle non-intrusive banner: "We noticed a link — open it in [App]?" that dismisses if ignored. Never open automatically.

## Anti-patterns

- Custom share UI that skips native destinations.
- In-app browser with no "Open in system browser" action — traps users.
- Speculative clipboard reads on app launch.
- Recommendations without a "Why?" explainer.

## Related

- `./general.md` — widgets, integrations, cross-platform parity.
- `./safety-privacy.md` — clipboard and permission privacy.
- `./ai-automation.md` — personalization driven by recommendations.
- `./multimodal-input.md` — camera / voice / QR as fast utility entry points.
