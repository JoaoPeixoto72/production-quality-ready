# Forms

Forms are where intent turns into action. Every extra field, every ambiguous label, every delayed error costs conversions.

## Checklist

| Item | Guidance |
|---|---|
| Minimal data collection | Ask only what's needed now. Defer optional fields to profile. |
| Show / hide password | Eye icon on the right of the password field. Hidden by default. |
| Password strength | 4-level meter as user types. Requirements inline. |
| No repeated input | Pre-fill known data. Never ask twice (WCAG 3.3.7). |
| Autofill / password manager | Uses platform content-type hints. Paste is always allowed on password fields. |
| Correct keyboard type | Email → email keyboard, Phone → number pad, URL → URL keyboard, OTP → number pad + autofill. |
| Enter key label | "Next" to advance focus, "Done" / "Search" to submit. |
| Auto-format input | Phone numbers, cards, dates format as the user types. |
| Inline validation | On blur, not only on final submit. Never on every keystroke for slow rules. |
| Labels above fields | Visible labels, not placeholder-only. Placeholders are hints, not labels. |
| Multi-step progress | "Step 2 of 4" indicator on multi-screen flows. User can go back. |
| Error recovery | On failed submit: scroll to first error, keep all data, highlight the offending field. Never wipe the form. |
| Alternative input methods | Voice / camera / QR / OCR offered where they save typing (see `./multimodal-input.md`). |

## Keyboard type reference

| Input | iOS `textContentType` | Android `inputType` |
|---|---|---|
| Email | `emailAddress` | `textEmailAddress` |
| Phone | `telephoneNumber` | `phone` |
| One-time code | `oneTimeCode` | (autofill hint) |
| Full name | `name` | `textPersonName` |
| Password | `password` | `textPassword` |
| New password | `newPassword` | — |

## Patterns

- **Progressive disclosure.** Split long forms into steps. 5–6 fields per screen max.
- **Smart defaults.** Pre-select the common option. Pre-fill country from IP. Pre-select current year for expiry.
- **Value-first over form-first.** Ask for account only after the user has experienced something.

## Anti-patterns

- Placeholder as label (disappears on focus, fails contrast, breaks screen readers).
- Disabling paste on password fields.
- Wiping the form on validation error.
- Asking for the phone-number country code manually when you can detect the locale.

## Related

- `./error-handling.md` — validation error formulas, inline error patterns.
- `./content.md` — label and placeholder writing.
- `./accessibility.md` — accessible authentication, redundant entry.
- `./multimodal-input.md` — camera / voice / scan for form fields.
