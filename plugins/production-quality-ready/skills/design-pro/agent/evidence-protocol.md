# Evidence Protocol

Every finding has three attributes: **what it is**, **where you saw it**, and **how certain you are**.

## The three confidence levels

- **Observed** — you saw the specific element in the source material (screenshot, code, running app, spec). Cite the artifact (file:line, screen name, region of image).
- **Inferred** — you deduced the finding from evidence you did see, but did not see the element itself. State the inference chain in one sentence.
- **Unknown** — the finding requires evidence you cannot obtain in this session (screen-reader behavior from a static screenshot, offline behavior without running the app, tap target from a rasterized image without scale). Mark `Unknown — needs testing`. This is not a failure.

## Citation format

- Screen: `Screen: <name>`
- Region of a screenshot: `Screen: <name>, region: <top-left,bottom-right> or verbal description`
- File: `` `path/to/file.tsx:120–142` ``
- Component: `Component: <ComponentName>`
- Spec / doc: `Spec: <title>, section <n>`

## Rules

1. Every `Fail` verdict must cite at least one Observed or Inferred piece of evidence.
2. Every `Blocker` severity requires Observed evidence. No Blockers from inference.
3. When an item cannot be judged from the provided material, mark verdict `N/A`, confidence `Unknown`, and add "needs testing" in the evidence column.
4. Do not restate the checklist as evidence. "The screen does not follow WCAG 2.2 2.5.8" is not evidence; "Screen: Sign-up, region: primary CTA — measured ~20×20 dp against a 24×24 dp requirement" is.
5. Screenshots are lossy. If a finding depends on font size, contrast, or pixel measurements, either use `Inferred` with a clear caveat, or mark `Unknown` and request the running app or the design tokens.

## Anti-patterns

- Universal citations like "throughout the app" — not evidence.
- "Common issue in Material apps" — that's a prior, not an observation.
- Citing WCAG rule numbers without pointing at the specific place the rule is violated.
- Escalating a Minor finding to Major because there are "many instances" that you did not enumerate.
