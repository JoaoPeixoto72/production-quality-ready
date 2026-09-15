# Accessibility

Accessibility is a quality floor, not a checklist. Contrast helps users in sunlight. Large hit areas help users on a moving bus. Clear labels help distracted users. Design for the edges and the center benefits too.

## Checklist

| Item | WCAG | Guidance |
|---|---|---|
| WCAG 2.2 AA compliance | — | Current standard since October 2023. Legal bar under EAA (June 2025) for EU. |
| Text contrast | 1.4.3 AA | 4.5:1 normal text. 3:1 large text (18sp or 14sp bold). |
| UI component contrast | 1.4.11 AA | 3:1 for icons, borders, focus indicators. |
| Target size (minimum) | 2.5.8 AA | 24×24 CSS px floor. Design targets: 44×44pt (Apple HIG), 48×48dp (Material). The 44px criterion is 2.5.5 AAA. |
| Focus order logical | 2.4.3 A | Tab and D-pad order matches the visual reading order. |
| Focus not obscured | 2.4.11 AA | Focused element at least partially visible — never fully hidden by sticky UI or overlays. |
| Screen reader labels | — | All interactive elements have accessibility labels. Custom actions replace gesture shortcuts. |
| Color-blind safe | 1.4.1 A | Color is never the only differentiator. |
| Reduce motion | 2.3.3 AAA | AAA formally, platform expectation on iOS/Android. Decorative motion is simplified when the flag is set. |
| Adjustable text size | — | Supports Dynamic Type (iOS) and sp units (Android). Tested at 200%. |
| Dark and light both meet contrast | — | Both themes independently pass 1.4.3/1.4.11. |
| Motor impairment support | — | Switch Control (iOS) / Switch Access (Android) reaches every interactive element. |
| Accessible authentication | 3.3.8 AA | No cognitive puzzles to sign in. Paste and autofill always allowed. |
| Redundant entry | 3.3.7 A | Never ask twice for information already given in the same flow. |
| Consistent help | 3.2.6 A | Help mechanism is in the same location on every screen where it appears. |
| Dragging alternative | 2.5.7 AA | Drag actions have a single-pointer alternative. |
| Thumb-zone reachability | — | Critical actions in the bottom 40% of mobile screens. |

## Testing approach

The single most effective test: complete every primary flow with the screen reader on and your eyes closed. If you cannot, it fails. Automated tools (Accessibility Inspector, Accessibility Scanner, axe) catch roughly 30% of real issues — a starting point, not a review.

## Platform APIs

- **iOS:** `accessibilityLabel`, `accessibilityHint`, `accessibilityTraits` (.button/.header/.link), `UIAccessibility.isReduceMotionEnabled`, `UIFont.preferredFont(forTextStyle:)`.
- **Android:** `contentDescription`, `importantForAccessibility`, `AccessibilityManager.isEnabled()`, `sp` units for user-scalable text.
- **Web:** ARIA landmarks and roles; `prefers-reduced-motion`, `prefers-contrast`, `forced-colors` media queries.

## Evidence rules for this guide

Contrast ratios estimated from a JPEG must be marked `Inferred` (see `../agent/evidence-protocol.md`). Screen-reader behavior from a static image is always `Unknown` — needs running app.

## Anti-patterns

- Citing WCAG rule numbers without pointing to the specific violation.
- Escalating a Minor finding to Major because "there are many instances" the reviewer did not enumerate.
- Treating platform HIGs as if they lower the WCAG floor.

## Related

- `./visual-design.md` — the design system that shapes contrast and hit areas.
- `./forms.md` — accessible validation, autofill, redundant entry.
- `./content.md` — plain language as an accessibility requirement.
- `../agent/visual-inspection.md` — measurement caveats when only screenshots are available.
