# UX of Agent-Driven Products

This is different from `./ai-automation.md`, which covers AI features embedded in a traditional product (a "summarize" button, a smart filter, a recommendation row). This guide is for products where the AI **is** the surface — the user states an intent and the product plans, acts, and reports.

## Checklist

| # | Item | Guidance |
|---|---|---|
| 1 | **Autonomy level is visible** | The user always knows whether the agent is *suggesting*, *asking to act*, or *acting*. Never mix modes silently. |
| 2 | **Intent capture is explicit** | The agent restates the user's goal before starting long work. Not "understood" — the actual goal in one sentence, so the user can correct it. |
| 3 | **Plan preview before expensive actions** | Any action that costs money, time, or is destructive shows a plan step the user can approve, edit, or reject. |
| 4 | **Reversibility is stated up front** | For every action, the UI states whether it is reversible, and if so, how. Non-reversible actions require explicit confirmation. |
| 5 | **Execution state is legible** | While the agent runs, the user sees: what step is active, what has completed, what is queued. Not a spinner. |
| 6 | **Partial completion is honest** | If the agent finished 4 of 6 steps and got stuck, the report says exactly that, names the failed step, and offers a next action. Never claim success on partial results. |
| 7 | **Tool errors surface with context** | When a tool call fails, the UI shows which tool, the error, and what it means for the goal — not a raw stack trace, not a generic "something went wrong". |
| 8 | **Long-running tasks show progress you can leave** | For tasks over ~30s, the user can navigate away and be notified on completion. Progress must survive a page reload. |
| 9 | **Transparency budget** | The agent explains enough to be trusted, not enough to drown the user. Default: one-line rationale per major decision; details on demand. Never expose raw chain-of-thought. |
| 10 | **Memory is inspectable** | If the agent remembers things across sessions, the user can view, edit, and delete what it remembers. |
| 11 | **Permissions are scoped** | The agent asks for access at the moment it needs it, not up front. Each permission states the specific reason. |
| 12 | **Previews before writes** | For file edits, message drafts, API calls with side effects: show the diff/draft/payload before executing. |
| 13 | **Undo is real** | "Undo" reverts state, not just hides the notification. If undo is impossible, do not offer it. |
| 14 | **Handoff to human is graceful** | The agent knows when to stop and hand back. The user is not blocked waiting for a clarification that never came. |
| 15 | **Multi-agent orchestration is legible** | When subagents run, the user sees the tree, not a mass of parallel spinners. Each subagent has a scope and a status. |
| 16 | **Failure state is a first-class screen** | Not a red banner over the normal UI — a dedicated view that explains what happened, what state the world is in now, and what to do next. |
| 17 | **Cost and consumption are visible** | Tokens, credits, minutes, API calls — whatever the user is spending — shown in-flow, not hidden in a settings page. |
| 18 | **Agent identity is stable** | Same tone, same capabilities, same limits across sessions. Personality drift is a defect. |
| 19 | **Silence is a signal** | If the agent has nothing to say, it says nothing. It does not fill space with "processing…", "thinking…", "let me analyze that…". |
| 20 | **Consent for autonomy escalation** | If the agent wants to move from "suggest" to "act autonomously" for a class of tasks, it asks once, per class, and the user can revoke. |

## Patterns

**The confirmation ladder.** Match confirmation weight to action weight: informational (no confirm) → reversible write (toast with undo) → irreversible or expensive (modal preview with explicit approve) → destructive or external (typed confirmation).

**The plan surface.** For any multi-step action, render the plan as a checklist the user can edit before running. Steps become live during execution. The plan is the receipt.

**Progressive trust.** Start every new capability in "suggest" mode. Promote to "act with confirmation" after N successful confirmations. Promote to "act autonomously" only with an explicit user setting, per capability, revocable.

**The two-clock rule.** Show two clocks for long-running work: elapsed time (facts) and estimated remaining (best guess, honestly labeled). Never show a single misleading progress bar that stalls at 90%.

**Failure symmetry.** If an action's success state is a specific screen with next actions, its failure state must be too. A failed run without a "what now" screen is a bug.

## Anti-patterns

- Streaming raw chain-of-thought as "transparency". It's noise; it also breaks trust when the model contradicts itself mid-stream.
- "The agent is thinking…" as the only feedback for 20 seconds.
- Undo that only dismisses the toast.
- Auto-executing irreversible actions because "you already confirmed in a previous turn".
- Multi-agent flows where the user can only see the top-level agent and has no way to inspect subagent state.
- Persistent memory the user cannot see or delete.
- Personality shifts between sessions or between capabilities.

## Related

- `./error-handling.md` — failure screens, undo, confirmation dialogs.
- `./safety-privacy.md` — permissions, consent, memory boundaries.
- `./notifications.md` — long-running task notifications.
- `../agent/human-in-the-loop.md` — when to ask vs act.
- `../agent/verification.md` — post-action verification the *product* should do before claiming success.
- `../agent/uncertainty.md` — how the agent should behave when confidence is low (say less, offer options).
