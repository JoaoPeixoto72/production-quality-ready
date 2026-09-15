# Tool Strategy

When to reach for a tool during a UX review, and which one. Loaded when a guide's finding depends on evidence a tool can produce.

## Decision table

| Situation | Tool |
|---|---|
| Need to see the running app | Computer use / preview in the IDE (Antigravity computer use, Claude Code browser, Codex sandbox). |
| Need to read code | Grep / read on the specific files. Do not load the whole repo. |
| Need a token value | Design system source (theme file, tokens JSON), not a screenshot. |
| Need to verify contrast / target size | Run the accessibility tool in the IDE. Do not estimate from JPEG. |
| Need a WCAG citation | Reference `../references/accessibility.md`, otherwise the W3C page. |
| Need to check platform behavior | Read the platform HIG / Material spec once, do not restate general knowledge. |
| Need real user data | Ask the user. Do not fabricate. |

## Rules

- One tool call per question. Do not chain speculative calls.
- If a tool fails, do NOT retry with identical arguments. Change the query or ask.
- If the required tool is not available in this environment, mark the dependent findings `Unknown — needs testing (tool: <name>)`.
- Do not use a tool to confirm a claim you already have Observed evidence for.

## Anti-patterns

- Running "grep -r ." to explore. Grep for the specific term the finding depends on.
- Loading the full component tree to check one style rule.
- Taking a screenshot of a screen you already have a screenshot of.
- Using a browser fetch to look up general UX advice mid-review. The guides already contain it.
