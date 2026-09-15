# Verification

Do the smallest, most specific check that could disconfirm your claim. Not a generic re-read.

## When to verify

Verify only when:

- A finding's Severity is `Blocker` and the evidence is `Inferred`.
- A recommended fix touches a shared component that other findings depend on.
- The user explicitly asked "are you sure about X".

Do NOT verify:

- Every finding you produced.
- Findings marked `Unknown` — those need external testing, not more thinking.
- Your own reasoning about a finding you already stated with Observed evidence.

## How to verify

1. Identify the exact claim to check. Write it as one sentence.
2. Pick the most direct source that could disprove it (the file, the design token, a fresh screenshot region).
3. Read that source once.
4. If confirmed, leave the finding as is. If disconfirmed, downgrade or remove the finding — do not "re-explain" it.
5. Do not narrate the verification to the user unless they asked.

## Post-implementation verification (when you also implemented a fix)

If the review turned into implementation (e.g. in Claude Code / Antigravity / Codex), verify what you changed:

- Load the changed screen or component.
- Confirm the specific behavior the fix targeted, not a general "does it look ok".
- If the change touched accessibility, run the accessibility tool available in the environment (axe, VoiceOver, TalkBack) — do not eyeball it.
- Note any regression risk in a separate "Verification" section of the report.

## What "sure" means

If a caller asks "are you sure": answer with confidence level from `evidence-protocol.md`, not with hedged prose. `Observed` claims stand. `Inferred` claims re-cite the inference. `Unknown` claims stay `Unknown`.
