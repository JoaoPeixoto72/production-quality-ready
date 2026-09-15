# Uncertainty

When to stop guessing and change strategy.

## The two failure modes

1. **Overconfident** — writing findings with the same tone regardless of evidence quality.
2. **Overcautious** — hedging every finding into uselessness.

Both are wrong. Use `Confidence` (`Observed` / `Inferred` / `Unknown`) to carry the calibration in the data, and write the prose plainly.

## Triggers to stop and ask

Ask ONE question when:

- The scope is genuinely ambiguous (two different interpretations, different reviews).
- A required input is missing and no safe default exists.
- The user's material contradicts itself in a load-bearing way.

Do NOT ask when:

- The default is obvious.
- The question is about style you can pick and note as an assumption.
- The material is thin but usable — produce a partial review with `Unknown` rows instead.

## Uncertainty in fixes

If you cannot construct the smallest-change fix with confidence, say so. Recommending a fix you are not sure about is worse than saying "the direction is X; the specific change depends on <thing you do not know>".
