# Quality Standard

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

> **Instrumento — ver `design-pro`.** Esta secção é a lista de verificação que
> o instrumento do `ui-system` corre para produzir candidatos que alimentam a
> régua do `design-pro` (WCAG 2.2 SC 2.4.7 "focus visible", SC 2.4.11 "focus
> not obscured", SC 2.5.3 "label in name"). O `ui-system` não fecha verdicts
> de UX/a11y — produz `candidate` / `clear` / `unproven` que o `design-pro`
> transforma em `PASS`/`FAIL`. Ver `CONTRACTS.md §2.3`.

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

> **Instrumento — ver `design-pro`.** Régua: WCAG 2.2 SC 1.4.3 (contraste
> texto 4.5:1), SC 1.4.11 (contraste UI 3:1), SC 2.5.3 (label in name), SC
> 2.5.8 (target size). O `audit_ui.py` produz candidatos por ΔL OKLCH sobre
> `tokens.css`; **não decide `PASS` de contraste** — pixels renderizados só
> se vêem com screenshot + amostragem perceptual, que é instrumento do
> `design-pro`. Cortar esta secção era autoderrota (v1.2.1 do plano).

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
