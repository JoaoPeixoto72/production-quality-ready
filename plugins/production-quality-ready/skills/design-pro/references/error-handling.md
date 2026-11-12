# Error Handling

Every error is a broken promise. How you handle it decides whether the user forgives or leaves. Good error handling is preventive, informative, and always leaves a path forward.

## Checklist

| Item | Guidance |
|---|---|
| Destructive confirmation | Single dialog. Confirm button red on the right, Cancel on the left. Verb matches the action ("Delete", not "OK"). |
| Undo affordance | Snackbar with "Undo" for 5–7s after deletions and moves. Undo actually reverts state. |
| Empty state | Every empty screen follows the anatomy below. |
| Preventive inputs | Constrained inputs, smart defaults, early validation. |
| Descriptive errors | What failed + why (if useful) + what to do next. |
| Crash recovery | App restores previous state on relaunch. |
| Server errors | 5xx / timeout show human message + Retry. Never a raw stack trace. |
| Auth error | Redirect to login preserving the intended destination. |
| Permission denied | Explain and link to Settings. |
| Network error | Top banner + offline fallback (see `./network.md`). |

## Error-message formula

```
[What happened] + [Why, if it helps] + [What to do next]
```

Examples:
- "We couldn't save your post. Check your connection and tap Save again."
- "Your session expired. Sign in to continue."
- "This username is already taken. Try adding numbers or a different word."
- "Payment declined. Your card ending in 4242 was not charged. [Try another card]"

## Error types and UI patterns

| Type | Pattern |
|---|---|
| Validation | Inline, below the field, on blur |
| Recoverable server error | Toast or inline with Retry |
| Blocking server error | Full-screen error with Retry + Contact support |
| Auth error | Redirect to login, preserve destination |
| Permission denied | Explain + deep-link to Settings |
| Network error | Top banner + offline fallback |
| Content not found (404) | Friendly message + suggestions + path to Home |
| Crash | Offer to report + restore previous state |

## Empty-state anatomy (canonical)

Other guides cite this section — do not restate it in `./search.md`, `./visual-design.md`, `./help-onboarding.md`.

Every empty state has four parts:

1. **Visual** — an illustration or icon matching the app's style.
2. **Heading** — short, specific: "No saved articles yet".
3. **Message** — one line describing what this space is for.
4. **Action** — optional primary button inviting the first step: "Browse articles".

Variants:

| Variant | Framing |
|---|---|
| First use | Invite the first action ("Add your first task") — never a bare empty list |
| No search results | "No results for X" + spelling suggestion + related categories |
| Error-caused | Explain the failure + Retry — do not disguise an error as an empty state |
| Cleared / completed | Celebrate: "All caught up" |

Never a dead end: every empty state offers a next step or a path back.

## Undo vs confirm

| Use undo when | Use confirm when |
|---|---|
| Action is reversible | Action is permanent |
| Cost of a mistake is low | Cost of a mistake is high |
| Speed matters | User should slow down |
| Example: archive a message | Example: delete an account |

## Anti-patterns

- "Undo" toast that only dismisses itself.
- "OK" as the button on a destructive dialog.
- Blank screen with no explanation instead of an error state.
- Raw error codes / stack traces exposed to users.
- Confirmation dialogs asking to confirm reversible actions (breeds dialog blindness).

## Related

- `./content.md` — error tone and microcopy.
- `./network.md` — connectivity-specific errors.
- `./forms.md` — inline validation.
- `./ai-agent.md` — failure state for products that are agents.
- `./consent-and-autonomy.md` — undo and reversibility rules for agent-taken actions.
