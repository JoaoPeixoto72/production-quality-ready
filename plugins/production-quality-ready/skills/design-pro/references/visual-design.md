# Visual Design

Visual design communicates hierarchy, state, and intent. Every spacing decision, color choice, and animation is a signal the user reads.

## Checklist

| Item | Guidance |
|---|---|
| Touch target hit area | 44×44pt (iOS), 48×48dp (Android), 24×24 CSS px minimum (WCAG 2.5.8 AA). Hit area, not visual size. |
| Font readability | Body copy at 16–17sp. Line height 1.4–1.6. Roles below Body are supporting text. |
| Text hierarchy | Max 3 levels: title / body / caption. Use weight and size, not color alone. |
| Semantic color | Green success, red errors and destructive, yellow warnings. Consistent across the app. |
| Color is a secondary signal | Never the only differentiator — pair with icon, label, or shape. |
| Active vs inactive | Communicated by opacity or shape change, not color alone. |
| Row spacing | 8pt padding between list items. Rows 56–72dp tall. |
| Micro-interactions | Button press feedback under 100ms. State transitions ≤ 300ms. |
| Reduce-motion respected | Decorative animations disabled or simplified when the OS flag is set. |
| RTL layout | Layout mirrors and directional icons flip for right-to-left languages. |
| 8pt grid | All spacing values are multiples of 4 or 8. |
| Safe areas | Background extends into notch / Dynamic Island / camera cutout. Content respects safe areas. |
| Dark mode palette | Dedicated palette with elevated surfaces. Not an inverted light theme. |
| Consistent dialogs | Alerts and modals styled the same everywhere. |
| Consistent elevation | Overlays, cards, sheets each have a distinct elevation level. |
| Image zoom | Pinch-to-zoom supported on primary images. |
| Image gallery | Swipe between images supported where multiple exist. |
| Universal icons | Meaning readable without a label for common icons. Add a label otherwise. |
| Transitions match hierarchy | Push, modal, dismiss animations reinforce direction of navigation. |

## Spacing tokens

| Token | Value | Use |
|---|---|---|
| space-1 | 4pt | Icon gap, tight padding |
| space-2 | 8pt | Inline padding, list gap |
| space-3 | 12pt | Component inner padding |
| space-4 | 16pt | Section padding, standard margin |
| space-6 | 24pt | Card padding, screen edge margin |
| space-8 | 32pt | Section separator |
| space-12 | 48pt | Large section gap |

Touch-target minimums are hit areas, not spacing tokens.

## Typography — iOS (HIG-derived)

| Role | Size | Weight |
|---|---|---|
| Display | 34sp | Bold |
| Title 1 | 28sp | Bold |
| Title 2 | 22sp | Semibold |
| Headline | 17sp | Semibold |
| Body | 17sp | Regular |
| Callout | 16sp | Regular |
| Subhead | 15sp | Regular |
| Footnote | 13sp | Regular |
| Caption | 12sp | Regular |

## Typography — Android (Material 3)

| Role | Size | Weight |
|---|---|---|
| Headline Medium | 28sp | Regular |
| Title Large | 22sp | Regular |
| Title Medium | 16sp | Medium |
| Body Large | 16sp | Regular |
| Body Medium | 14sp | Regular |
| Label Large | 14sp | Medium |
| Label Small | 11sp | Medium |

Use each platform's native scale, not one forced on both.

## Patterns

- **Color as secondary signal.** Pair with an icon, label, or shape so color-blind users get the same information.
- **Elevation communicates layers.** Overlays vs cards vs sheets must be visually separable, especially in dark mode.
- **Motion has meaning.** If a motion isn't reinforcing hierarchy or state change, cut it.

## Anti-patterns

- Body copy below 15sp.
- Success/error states signaled by color only.
- Screen transitions with no direction.
- Dark mode built by inverting light-mode tokens.

## Related

- `./accessibility.md` — contrast ratios, Dynamic Type, reduce-motion (WCAG floors).
- `./content.md` — the words that fill the components.
- `./error-handling.md` — canonical empty-state standards.
- `../agent/visual-inspection.md` — how to cite regions of a screenshot in a finding.
