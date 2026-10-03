# Quality Standard

## Contents

- Definition of done
- Architecture
- Interaction
- Accessibility
- Responsive design
- Content states
- Visual quality
- Migration quality
- Profile-specific checks
- Verification report

## Definition of done

A substantial UI task is done only when the relevant categories below pass.

## Architecture

- Application code imports the owned UI package.
- Direct Base UI imports are confined to the configured UI source.
- External styled systems were not introduced without approval.
- Existing components were reused where appropriate.
- Public APIs do not unnecessarily leak upstream types.
- Theme decisions are not hardcoded in application components.
- No CSS selector compares Base UI boolean state attributes to `"true"` or
  `"false"`.
- The theme attribute is present on the root element at runtime with a dialog
  open, not only in static HTML.
- `scripts/audit_ui.py` reports no open `error` findings.

## Interaction

> **Instrument — see `design-pro`.** This checklist produces candidates for
> `design-pro`'s ruler (WCAG 2.2 SC 2.4.7, SC 2.4.11, SC 2.5.3). `ui-system`
> closes no UX/a11y verdict: it emits `candidate` / `clear` / `unproven`, and
> `design-pro` turns them into `PASS`/`FAIL` (`CONTRACTS.md §2.3`).

- Controls work with keyboard.
- Focus is visible.
- Focus enters and leaves overlays correctly.
- Escape and outside dismissal behave deliberately.
- Disabled controls do not perform actions.
- Loading states prevent duplicate actions where needed.
- Controlled and uncontrolled behavior is not accidentally mixed.
- Overlay backdrops are direct children of the Portal, default to
  `position: fixed`, and only switch to the documented iOS Safari absolute
  fallback together with `body { position: relative; }`.

## Accessibility

> **Instrument — see `design-pro`.** Ruler: WCAG 2.2 SC 1.4.3 (text contrast
> 4.5:1), SC 1.4.11 (UI contrast 3:1), SC 2.5.3 (label in name), SC 2.5.8
> (target size). `audit_ui.py` yields candidates by OKLCH ΔL over `tokens.css`;
> it **never decides contrast `PASS`** — rendered pixels need a screenshot and
> perceptual sampling, which is `design-pro`'s instrument.

- Native HTML is preferred.
- Interactive elements have accessible names.
- Fields have labels and error relationships.
- Dialogs have meaningful titles.
- Icon-only buttons have labels.
- Color is not the only state indicator.
- Reduced motion is supported.
- Automated checks are supplemented by manual keyboard review.

## Responsive design

Test at least narrow mobile, wider mobile, tablet or constrained desktop,
standard desktop, and wide desktop where relevant.

## Content states

Test default, loading, empty, partial data, error, success, disabled, long
content, missing optional data, large numeric values, and many list items.

## Visual quality

- Hierarchy is clear without relying on decoration.
- The most important user action is evident.
- Repetition has deliberate rhythm.
- Surfaces have semantic purpose.
- Typography has a controlled scale.
- Spacing communicates grouping.
- Color has a role.
- Motion communicates change.
- The result does not resemble an unrelated generic template.

## Migration quality

- Existing behavior is preserved or changes are documented.
- Routes and payloads remain valid.
- Validation remains intact.
- Analytics and test hooks are preserved.
- Legacy removal is supported by repository search and tests.
- Migration steps remain reviewable.

## Profile-specific checks

When a repository selects a profile, run that profile's extra checks in
addition to this generic standard.

## Verification report

Never claim a test passed if it was not run.

Use:

```text
PASS: command ran successfully
FAIL: command ran and failed
NOT RUN: unavailable or outside scope
MANUAL REVIEW NEEDED: cannot be verified automatically
```
