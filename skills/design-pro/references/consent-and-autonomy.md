# Consent and Autonomy

When an agent takes actions on the user's behalf, consent stops being a one-time onboarding checkbox and becomes a per-action, per-scope, revocable contract. This guide is the canonical home for that contract.

Related but different: `./safety-privacy.md` covers consent for **data collection**; this guide covers consent for **actions**.

## Checklist

| Item | Guidance |
|---|---|
| Confirmation weight matches action weight | Informational (no confirm) → reversible write (toast + undo) → irreversible / expensive (modal preview + approve) → destructive / external (typed confirmation). |
| Plan preview before expensive actions | Any action costing money, time, or touching external systems shows a plan the user can approve, edit, or reject. |
| Dry-run for state-changing actions | Where technically possible, offer a dry-run that shows the exact diff or side-effects. |
| Per-action reversibility stated | Every action's UI states whether it is reversible and how. |
| Real undo | "Undo" restores state, not hides the toast. If reverting is impossible, do not offer undo. |
| Revocable scopes | Every autonomy grant is visible in Settings and revocable in one action. |
| Time-boxed autonomy | Autonomy grants can be set for a duration (this session / 24h / until revoked). |
| Autonomy tier is visible | The user always sees whether the agent is *suggesting*, *asking before acting*, or *acting autonomously* for a class of tasks. |
| Escalation asks per class | Promoting from "ask" to "act autonomously" requires an explicit consent per capability class, not a blanket "enable all". |
| Consent traces auditable | The user can view: what was authorized, when, for how long, and what actions ran under it. |
| Cost / side-effect disclosure | Financial cost, credit / token spend, third parties contacted — surfaced in the plan preview, not hidden. |
| Multi-user consent respected | Actions affecting other users (send message, invite, share) require explicit per-action consent even in autonomous mode. |
| Physical-world consent floor | Actions that trigger real-world side effects (payment, purchase, physical device, message send) always require explicit confirmation regardless of autonomy tier. |
| Refuse path is a first-class outcome | The user can always say "stop" or "cancel" during a plan or execution and the agent gracefully unwinds. |

## The confirmation ladder

Match confirmation weight to consequence:

| Class | Example | UX |
|---|---|---|
| Informational | Read a public page | No confirm |
| Reversible write | Save a draft, add a favorite | Toast + Undo |
| Non-trivial reversible | Rename a file, move an email | Inline confirm or preview |
| Irreversible / expensive | Send an email, place an order, delete a file | Modal preview + explicit approve |
| Destructive or external | Delete an account, wire money, mass-mail contacts | Typed confirmation ("type DELETE to continue") |

The ladder is model-agnostic. It applies to human-initiated actions and agent-taken actions alike, but the *default* for agent-taken actions should sit one rung higher on the ladder than the same action a human triggers directly.

## Plan preview format

Every plan preview carries: steps in order, expected duration, cost / credits / tokens, third parties involved, reversibility per step, and the "confirm / edit / cancel" set. The plan is the receipt: after execution, the same UI shows what actually ran, with per-step outcomes.

## Autonomy tiers

| Tier | Behavior | Default for |
|---|---|---|
| Suggest | Agent proposes; user acts | New capability, unfamiliar user |
| Ask | Agent asks before each action | Capabilities used more than a few times |
| Act (bounded) | Agent acts autonomously within named limits (max cost, max side-effects, allowed tools) | Explicit opt-in per capability class |
| Act (unbounded) | Rare; usually inappropriate | Very narrow, well-understood capabilities |

Promotion between tiers is per capability class, requires an explicit consent step, and is time-boxable. Demotion is instant and does not require justification.

## Revocation and audit

Settings > Autonomy shows: every capability the agent has, its current tier, its scope, its expiry (if time-boxed), and a log of the last N actions run under it. Revocation is single-click.

## Anti-patterns

- Blanket "enable autonomous mode" toggle. Autonomy is per capability class, never global.
- Undo that only dismisses the toast. Either the state reverts or the UI does not offer undo.
- Plan preview that hides cost or third-party involvement.
- Escalating to "act autonomously" the moment the user approves one action.
- Time-boxed autonomy that silently renews.
- Confirmation dialogs on reversible actions ("Are you sure you want to save?") — breeds dialog blindness and makes real confirmations unread.
- Physical-world actions (payment, message send) executed autonomously without per-action consent.

## Related

- `./ai-agent.md` — the broader UX of products that are agents.
- `./safety-privacy.md` — data-collection consent (distinct from action consent).
- `./error-handling.md` — undo mechanics, failure-state screens.
- `./settings.md` — where the autonomy panel lives.
- `../agent/human-in-the-loop.md` — the agent-side decision table for when the agent should ask.
- `../agent/uncertainty.md` — how to surface low-confidence proposals to the user.
