# Visual Inspection

How to read screenshots and running UIs for a review. Referenced from the guides that judge visual output (`references/visual-design.md`, `references/accessibility.md`, `references/navigation.md`, `references/content.md`, `references/ai-agent.md`).

## Before you look

State what artifact you have:

- A single screenshot (static, unknown scale).
- A screenshot set (multiple states, still static).
- A running app in a computer-use / preview surface (interactive).
- A Figma/design source (has real tokens and measurements).
- Code only.

Each has different reliable readings. A raster screenshot cannot tell you tap-target size in dp; a running app can. A design source can tell you exact colors; a JPEG cannot.

## How to read a screenshot

1. **Bound the image.** Note the reported resolution and, if known, the device class. If the scale is unknown, state that any measurement is `Inferred`.
2. **Segment the image.** Identify header, body, footer / bottom bar, floating elements, and overlays. Cite them by name in findings.
3. **Read the copy verbatim.** Do not paraphrase button labels. If the text is unclear (low resolution, small size), say so.
4. **Check the semantic layers separately**: layout, typography, color, iconography, spacing, hierarchy, state (default / focused / disabled / error).
5. **Cite regions in findings** using either coordinates ("top-right of the header") or component names visible in the screenshot.

## How to read a running app (computer-use / preview)

1. Load the entry screen. Screenshot it before you interact.
2. Follow the user journey the review targets — do not click at random.
3. Capture the state at each decision point.
4. Interact with each control once to verify it responds. Do not stress-test.
5. If you leave the app in a modified state (form filled, item added), revert it before finishing.

## What NOT to do

- Do not report contrast ratios from a JPEG without stating the estimation method — say "estimated from screenshot; verify with design tokens".
- Do not measure touch targets in pixels from a screenshot with unknown DPR.
- Do not describe animations from a still image.
- Do not report screen-reader behavior from any static image. Mark `Unknown — needs testing`.
- Do not caption a finding with generic image descriptions ("a mobile app screen"). Cite the actual region.

## When the visual evidence is ambiguous

Prefer `Unknown` over a plausible guess. A review with several `Unknown` rows and a specific "needs the running app to verify" note is more useful than one with confident wrong findings.
