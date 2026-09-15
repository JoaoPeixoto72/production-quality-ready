# Agent Operating Model

How the agent should approach a UX review. Loaded from the reference guides by pointer, not repeated inside each guide.

## The five stances

1. **Evidence-first.** No finding without a source. If you cannot cite it, mark `Unknown`.
2. **One pass.** Read → decide → write. Do not re-run the checklist or rewrite the report. Targeted checks of a single claim follow `agent/verification.md`.
3. **Smallest change.** When recommending fixes, propose the smallest change that materially improves the experience, not a redesign.
4. **Named platforms.** iOS ≠ Android ≠ Web. Cite the specific platform convention when a finding depends on one.
5. **Silent by default.** If you have nothing to say about a checklist item, mark it `N/A`. Do not fabricate coverage.

## The review turn

```
Scope   → identify (screen | flow | feature | app).
Guides  → route via the SKILL.md routing table, within its load cap.
Evidence→ gather per agent/evidence-protocol.md. If visual, per agent/visual-inspection.md.
Apply   → run each guide's checklist ONCE.
Report  → templates/review-report.md.tmpl.
Stop.
```

The word "Stop" is load-bearing.

## What you must not do

- Do not narrate your reasoning process to the user.
- Do not add a blanket "final verification" or "double-check" pass over findings you already wrote. Checking one specific claim is a different thing, governed by `agent/verification.md`.
- Do not suggest that the user "consider" doing something. Say what to do or don't include it.
- Do not include severity you cannot support. `Blocker` requires evidence of breakage, not intuition.
- Do not expand scope. If asked about the checkout, don't also review the profile screen.

## When the material is insufficient

You have three legitimate outputs:

- **A partial review** with `Unknown` confidence on the items you cannot verify.
- **A single ONE-question ask** with concrete options, if the missing input is the critical dependency.
- **A refusal to guess**, stated plainly, when neither of the above helps.

Producing a confident-looking review from thin material is the worst outcome.
