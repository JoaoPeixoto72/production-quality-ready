# Cross-Skill Orchestration

How multiple reference guides interact within one review.

## Precedence

When two guides disagree about the same item:

1. Platform-specific rule wins over generic advice.
2. Accessibility (WCAG 2.2) is a floor — other guides' aesthetic preferences do not override it.
3. Safety/privacy is a floor — content and utility guides do not override it.
4. When two guides recommend contradictory changes for the same element, pick one, cite both, and note the tradeoff in the fix.

## Deduplication

If two guides would produce the same finding (e.g., `references/accessibility.md` and `references/visual-design.md` both flag low contrast), file it once, under the more specific guide. Reference from the other row.

## Cross-references (canonical homes)

- **Empty-state standards** — `references/error-handling.md`. All other guides reference it.
- **Notification granularity** — `references/notifications.md`. `references/settings.md` references it.
- **In-app language and clear cache** — `references/settings.md`. Not `references/general.md`.
- **10-second comprehension** — `references/help-onboarding.md`. Not `references/user-account.md`.
- **WCAG 2.2 rule text** — `references/accessibility.md`. All other guides cite by rule number.

## Anti-patterns

- Restating the same finding under three guides to "raise its priority". Severity is the priority signal.
- Loading two guides that clearly cover the same ground (e.g., `references/forms.md` + `references/content.md` for a review that is really about validation copy — pick one).
