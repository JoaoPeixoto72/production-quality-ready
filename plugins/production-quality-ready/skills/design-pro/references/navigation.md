# Navigation

Navigation is the app's skeleton. When it is invisible and predictable, users feel in control. When it is broken, they leave.

## Checklist

| Item | Guidance |
|---|---|
| Home reachable everywhere | Home tab or logo returns to root from any screen. |
| Persistent primary nav | Tab bar / bottom nav visible on primary screens. |
| Primary content reachable without getting lost | Every primary destination has an obvious path from home. Tap count is a smell, not a threshold: a long path that is signposted at every step beats a short one through an ambiguous menu. Do not file a finding on depth alone. |
| Current location indicator | Active tab highlighted. Deep screens carry a clear title or breadcrumb. |
| Android back button correct | Follows the back stack; never exits the app unexpectedly. |
| Back / close on every pushed screen | Always in the top-left corner. |
| Flow matches mental model | Screen order matches the user's task sequence, not the DB schema. |
| Deep link support | Every major screen has a URI scheme / Universal Link. |
| Tab bar badge accuracy | Badges match actual unread items and clear when viewed. |
| Content padded above tab bar | Content bottom respects tab bar and safe area. |
| Status bar visible in-app | Hidden only in full-screen media. |
| Modal vs push discipline | Push for hierarchy drill-down. Modal for interruptive tasks (create/edit/confirm). |
| Web: browser back works | For web / PWA, the browser back button follows the app's logical history. |

## Patterns

- **Bottom tab bar (iOS).** 3–5 items. Icon + label. Badges for counts. Never for destructive actions.
- **Side drawer (Android).** For 5+ top-level sections. Hamburger or left-edge swipe. Avatar and name at top.
- **Top nav bar.** Title left or centered. Max 2 action icons on the right. Back / close on the left.
- **Deep-linking strategy.** Every major content screen has a stable URI, so shares, notifications, and marketing land users on the exact screen.

## Anti-patterns

- Pushing a screen that should have been a modal — it breaks back-stack expectations.
- Nesting more than 2 levels of drill-down without a clear escape.
- Counting taps as the finding. The "3-tap rule" is folklore — its web ancestor, the 3-click rule, was refuted by UIE's click study (620 tasks, no relationship between click count and success or satisfaction). What makes users leave is not knowing where they are.
- Hiding search or account behind a hamburger on a content-heavy app.

## Related

- `./information-architecture.md` — the structure this navigation surfaces.
- `./notifications.md` — deep links notifications land on.
- `./general.md` — cross-platform navigation parity.
- `../agent/platform-adaptation.md` — iOS vs Android vs Web navigation baselines and back-gesture rules.
