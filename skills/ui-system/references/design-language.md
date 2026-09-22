# Design Language

## Core philosophy

The system should feel deliberate, calm, precise, and product-specific.

Consistency comes from shared proportions, interaction behavior, typography,
spacing logic, and semantic roles. It must not come from placing every piece of
content inside the same rounded card.

## Starter theme

The generic starter theme is called `studio`.

Its purpose is to provide a restrained starting point while the project's actual
visual identity is developed. Product-specific palette, typography, platform,
and domain rules belong to a selected profile, not to the generic core.

Starter characteristics:

- neutral surfaces;
- strong text hierarchy;
- moderate corner geometry;
- limited elevation;
- visible but controlled focus;
- comfortable controls;
- sentence-case interface text;
- borders used for structure;
- color reserved for action, status, and emphasis;
- motion used to clarify change.

If the repository selects a profile under `profiles/<name>/`, read that profile's
own design-language notes before applying product-specific visual rules.

## Fixed core

These remain consistent across themes:

- semantic component roles;
- keyboard behavior;
- focus visibility;
- component states;
- disabled behavior;
- loading behavior;
- public API;
- stable slot names;
- accessibility semantics;
- minimum interaction requirements.

## Theme-controlled expression

Themes may change:

- font families;
- type scale expression;
- colors;
- radius;
- borders;
- shadows;
- visual density within supported limits;
- motion personality;
- surface treatment;
- decorative details;
- component proportions where contracts permit.

## Typography

Use typography as hierarchy, not decoration.

Define:

- body;
- small;
- caption;
- label;
- heading levels;
- display text only when justified.

Avoid:

- all-caps labels by default;
- arbitrary font-size values;
- accenting one random word in a heading;
- excessive eyebrow labels;
- weak contrast between hierarchy levels;
- long line lengths.

Interface labels should use sentence case unless a specific language convention
requires otherwise.

## Surfaces

Use a surface only when it communicates a boundary, elevation, grouping, or
interaction region.

Do not automatically wrap:

- every metric;
- every section;
- every form group;
- every paragraph;
- every navigation item.

Alternatives include spacing, alignment, section headings, dividers,
background changes, typographic contrast, and grid placement.

## Geometry

Pills are appropriate for status, tags, compact filters, segmented controls,
and values whose shape communicates containment.

Pills are not the default shape for every button, every input, every
navigation item, or every panel.

## Motion

Prefer motion that explains where content came from, what opened, what closed,
what changed, and whether an action succeeded.

Avoid repetitive page-load fade-and-slide animations.

Respect reduced-motion preferences in core CSS.

## Content

Use specific interface copy.

Prefer:

- "Save changes"
- "Delete project"
- "Invite member"
- "Retry upload"

Avoid vague actions such as "Submit", generic "Continue", or "OK" when a
specific action can be named.

## Product-specific direction

For substantial new work, derive one characteristic visual idea from the
product's subject.

Examples:

- logistics: routes, schedules, movement, operational density;
- publishing: rhythm, editorial typography, annotation;
- finance: comparison, precision, confidence, data hierarchy;
- creative tools: canvas, layers, direct manipulation;
- archives: indexing, provenance, cataloguing.

Do not copy these examples mechanically.

## Theme and color scheme inheritance

- The core defines base semantic values in `:root` based on the starter theme (`studio`).
- A new custom theme inherits these semantic defaults as fallback values and should override the tokens that establish its identity (surfaces, accents, borders, typography, radius).
- Dark mode (`:root[data-color-scheme="dark"]`, `.dark`) operates as a color scheme axis that can combine with themes.

## Overlay infrastructure

- The rule `:where(body) { position: relative; min-height: 100dvh; margin: 0; }` exists as infrastructure for Base UI portals, dialogs, and backdrop positioning across mobile viewports (notably avoiding clipping in iOS Safari fallbacks).
- In projects that do not use portals, mount overlays inside a dedicated isolated container, or handle body constraints at the application layer, this rule can be adjusted.

