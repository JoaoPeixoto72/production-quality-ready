# Task Decomposition

Whole-app reviews are the failure case for one-shot reviews. Decompose them.

## When to decompose

- Scope = `app` (whole app / store readiness).
- Scope = `flow` with more than ~4 screens.
- User asked for "everything" without narrowing.

## How to decompose

1. Enumerate the surfaces: list every distinct screen or flow to review.
2. Group by shared category set (all forms, all navigation surfaces, all AI-agent surfaces).
3. Run one focused review per group, each with its own guide selection under the cap in `../SKILL.md`.
4. Aggregate at the end with a top-level Summary and Top fixes, referencing the per-group reports.

## Rules

- Never exceed the load cap for any one group.
- Never share findings across groups implicitly. If a finding recurs, cite each occurrence.
- The aggregate summary is 3–5 sentences, not a re-writing of every group summary.
- Top fixes across the whole app is still capped at 5. Rank across groups.

## Anti-pattern

The "mega review" — one report with 200 rows across every category, no ranking, no scope. This is what V2's `references/review.md` risked producing on 5.x models because they follow "apply each checklist" literally. V3 prevents it by capping selection and by requiring per-group runs on `app` scope.
