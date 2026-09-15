# Implementation Loop

When the review turns into implementation (fix requested and possible in-session).

## The loop

```
1. Restate the fix in one sentence.
2. Locate the smallest touch surface.
3. Make the change.
4. Run the specific check that verifies the fix (from agent/verification.md).
5. Observe the result.
6. If pass: report. If fail: adjust once. If still fail: stop and report.
```

Cap: **3 iterations, ever.** After the third failed attempt, stop and hand back to the user with a description of what you tried and why it did not work. This cap is model-agnostic and non-negotiable — Opus 5, GPT-5.6 Sol, and Gemini 3.8 Flash all tend to keep iterating on plausible-looking bad fixes.

## When to escalate immediately (no loop)

- The fix requires design decisions the user has not authorized.
- The fix touches shared components used outside the current scope.
- The change would remove functionality (even accidentally).
- You cannot construct the specific verification check.

## What NOT to do

- Do not "improve" adjacent code you were not asked to touch.
- Do not add tests unless the user asked. Verification ≠ writing tests.
- Do not refactor to a "better pattern" mid-fix.
- Do not commit or push. Leave the working tree ready for the user to review.
