# Content and UX Writing

Every word in the UI is a design decision. Good writing reduces friction, builds trust, and guides users to the next step. It carries the same weight as visual design.

## Checklist

| Item | Guidance |
|---|---|
| Plain language | ~7th-grade reading level. Short sentences and common words. |
| Data accuracy shown back | User-entered data validated and displayed correctly, never stale. |
| UGC distinct from editorial | Visually different container; never confuse a user quote with an app message. |
| Read / unread state | Bold title or colored dot. Not color alone. |
| Localization quality | Reviewed by native speakers. Machine translation alone is insufficient. |
| Content freshness | Outdated content flagged, archived, or removed on a defined threshold. |
| AI-generated content labeled | Consistent badge (sparkle icon widely recognized). Not buried in metadata. See `./ai-automation.md`. |

## Writing principles

**Be specific.**
- Avoid: "Something went wrong."
- Use: "We couldn't save your photo. Check your connection and try again."

**Write for the action, not the object.**
- Avoid: "Submit".
- Use: "Create account" / "Send message" / "Place order".

**Front-load the key information.**
- Avoid: "To complete your order, please enter your card details below."
- Use: "Enter your card details to complete the order."

**Be consistent.** One word per concept, everywhere.

## Microcopy patterns

| Context | Pattern |
|---|---|
| Button | Verb + noun: "Download report", "Add photo" |
| Destructive button | Specific verb: "Delete account", never "OK" |
| Placeholder | Genuine hint, not a repeated label: "Search by city or ZIP" |
| Error | What happened + how to fix |
| Success | Confirm action + suggest next step |
| Loading | What is loading: "Uploading photo…" |
| Empty state headline | Empathetic, forward-looking (anatomy in `./error-handling.md`) |

## Localization notes

- Never concatenate strings — use placeholders: `"Hello, %@"`, not `"Hello, " + name`.
- Leave 30–40% expansion space for German, Finnish, Russian.
- Date, time, number, currency: always platform formatters.
- RTL needs layout mirroring, not just text-direction switching.

## Anti-patterns

- Placeholder text as the only label (fails contrast, disappears on focus, breaks screen readers).
- "OK" on a destructive dialog.
- "Loading…" with no context on what is loading for over ~3s.
- Hard-coded date formats.

## Related

- `./error-handling.md` — error message formula and empty-state anatomy.
- `./forms.md` — labels, placeholders, validation copy.
- `./accessibility.md` — plain language as an a11y requirement.
- `./ai-automation.md` — AI content labeling and disclosure copy.
