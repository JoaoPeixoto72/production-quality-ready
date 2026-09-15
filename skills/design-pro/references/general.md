# General App Quality

The fundamentals every app needs regardless of domain. Reviewers, users, and store guidelines all expect them.

Priorities in the checklist:

- **Required** — launch blocker; app is not production-ready without it.
- **Recommended** — strong quality signal; most successful apps have it.
- **Optional** — differentiator; valuable for specific audiences, not universal.

## Checklist

| Item | Priority | Guidance |
|---|---|---|
| App name | Required | Memorable, spellable, searchable. Trademark-checked. |
| App icon | Required | Recognizable at 29×29pt. No text. Works on light and dark backgrounds. |
| Installation guide | Recommended | User clearly informed about install / activation. |
| What's new | Recommended | Changelog shown post-update. Plain language, not "bug fixes". |
| Splash screen | Required where applicable | Brand-colored, centered logo, under 2s. |
| Force update | Required | Mandatory update dialog for outdated versions with a clear update link. |
| Backup and restore | Recommended | User can back up and fully restore on reinstall. |
| OS language sync | Recommended | Language updates automatically when OS language changes. |
| Dark mode sync | Recommended | Follows OS setting without manual toggle. |
| Contact support | Required | A clear path to reach the team is available inside the app. |
| Cross-platform parity | Recommended | Core functionality consistent across supported platforms. |
| Version number visible | Required | In Settings or About. |
| Trial mode indicator | Required where applicable | Trial users see status and expiry clearly — cross-reference `commercial-readiness`. |
| In-app operation status | Required | Progress of ongoing actions visible while they run. |
| Cancel any async action | Recommended | Every async operation shows a cancel option while in progress. |

> **Escopo.** Linhas específicas de loja móvel — PWA icon, ASO metadata,
> Cloud sync, Background mode, Widget support, Storage location (SD card),
> In-app rating prompt, Status bar activity, Multitasking split-screen,
> Orientation, Pull-to-refresh, Ad removal, IAPs — foram removidas em
> `production-quality-ready` v1.3.0 do plano. Se o produto é uma app móvel de loja,
> re-adicionar por referência local do projecto. Para desktop, "Ship-ready
> baseline" desktop está coberto por `commercial-readiness` e este `general.md`.

## Key principles

- **Ship-ready baseline.** Required items are table stakes; failing any means "not ready".
- **Platform conventions matter.** iOS and Android users have different mental models — follow each.
- **Real devices, not simulators.** Simulators miss orientation, performance, real storage behavior.
- **Meaningful "What's new".** "Bug fixes and performance improvements" wastes the surface.

## Anti-patterns

- "What's new" text that reads "bug fixes and performance improvements" — wastes the store surface.
- Splash screen over 2 seconds — reads as a broken cold start, not a brand moment.
- Force-update dialog with no visible store link — traps users on an old build.
- App icon that includes text — unreadable at 29×29pt.
- Simulators-only QA — orientation, storage, and real-network failures slip through.
- Contact-support behind a link to a web form outside the app.
- Rating prompt on first launch, before the user has had a win.
- Cross-platform "parity" achieved by porting one platform's patterns to the other (iOS drawer on Android, Material FAB on iOS).

## Related

- `./settings.md` — in-app language, cache clearing, preferences.
- `./navigation.md` — deep links, back stack, hierarchy.
- `./notifications.md` — push permission and content quality.
- `./review.md` — the router for a full multi-category audit.
- `../agent/platform-adaptation.md` — cross-platform baselines (iOS 44pt, Android 48dp, Web Core Web Vitals).
