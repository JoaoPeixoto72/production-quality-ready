# Component Strategy

## Contents

- Choosing the implementation level
- Components verified in Base UI
- Not in Base UI
- Prefer Base UI even where HTML looks enough
- Always Base UI
- Confirming the API before writing code
- Component contract
- Variant discipline
- Size discipline
- Compound components
- Domain components
- New dependency policy

## Choosing the implementation level

Use the lowest level that is enough:

1. Native HTML.
2. An existing owned component.
3. An existing owned pattern.
4. Base UI, wrapped privately.
5. A new owned primitive, only when needed.
6. An application domain component.

## Components verified in Base UI

Checked against https://base-ui.com/llms.txt (v1.8.0); re-confirm against the
installed version before implementing.

Overlays and navigation: Dialog, Alert Dialog, Drawer, Popover, Tooltip,
Preview Card, Menu, Menubar, Context Menu, Navigation Menu, Toolbar,
Tabs, Toast.

Selection and input: Select, Combobox, Autocomplete, Input, Number Field,
OTP Field, Checkbox, Checkbox Group, Radio, Switch, Toggle,
Toggle Group, Slider.

Forms: Field, Fieldset, Form.

Structure and feedback: Accordion, Collapsible, Scroll Area, Separator,
Progress, Meter, Avatar, Button.

Utilities: CSP Provider, Direction Provider, mergeProps, useRender.

## Not in Base UI

These are owned, on native HTML:

Badge, Card/Surface, Skeleton, Spinner, Table/DataTable, Breadcrumb,
Pagination, Empty State, Stack, Inline, Grid, Container, Heading, Text,
Link, Textarea.

## Prefer Base UI even where HTML looks enough

| Component | Why not stay native |
|---|---|
| Field | Labelling, validation, and the label/error/description relation |
| Form | Consolidates the form's error handling |
| Fieldset | A styleable legend, notoriously hard in CSS |
| Button | Renderable as another tag, focusable when disabled |
| Input | Integrates with Field and Form |
| Separator | Correct semantics for screen readers |
| Progress, Meter | ARIA semantics and values |
| Avatar | Image fallback states |

A native `<button>` stays right for isolated actions outside forms. A bare
`<input>` in a real form is almost never right: it loses the relation with
label, description and error.

## Always Base UI

Never by hand: focus trap, dismissal, popup positioning, keyboard navigation
in collections, toast announcements, swipe gestures, virtual focus.
Undifferentiated work that is hard to get right.

## Confirming the API before writing code

In this order:

1. The installed package's types and code, and the lockfile.
2. `https://base-ui.com/llms.txt` for the component index.
3. The component's docs page with the `.md` suffix
   (`https://base-ui.com/react/components/select.md`), which returns Markdown.
4. Never generate props from memory.

The Tailwind examples in `llms.txt` are written for v4; convert if
`package.json` uses v3. Base UI asks for its docs to be treated as
authoritative over prior knowledge.

## Component contract

Before adding a reusable component, define:

```markdown
# Component name

## Purpose
What user problem it solves.

## Use when
Appropriate situations.

## Do not use when
Misuse cases and alternatives.

## Anatomy
Root, trigger, label, content, description, actions, and slots.

## Variants
Semantic variants only.

## Sizes
Supported sizes and why they exist.

## States
Default, hover, focus-visible, active, disabled, loading, invalid, open,
selected, checked, empty, or other relevant states.

## Behavior
Keyboard, pointer, touch, controlled and uncontrolled behavior.

## Accessibility
Native semantics, labels, descriptions, announcements, focus, and errors.

## Content
Copy and icon rules.

## Responsive behavior
How the component adapts.

## Tokens
Semantic and component tokens consumed.

## Upstream primitive
Native HTML or exact Base UI primitive.

## Testing
Unit, interaction, accessibility, and visual cases.
```

## Variant discipline

Add a variant when it expresses a reusable semantic distinction.

Good:

- primary;
- secondary;
- quiet;
- danger;
- success;
- warning.

Questionable:

- blue;
- gradient;
- glass;
- neon;
- rounded;
- shadow.

Visual styling belongs to themes.

## Size discipline

Do not create sizes without product use cases.

A common starting set:

```text
small
medium
large
```

Compact data-heavy products may need `x-small`. Marketing components may need
different primitives rather than oversized application controls.

## Compound components

Use compound components when consumers need to:

- rearrange sections;
- omit optional parts;
- insert custom content;
- control responsive composition;
- combine related subcomponents.

Keep simple wrappers for frequent common cases.

## Domain components

Domain components belong in applications unless they are reused across multiple
products.

Examples:

```text
InvoiceStatus
FleetHealthSummary
PublicationIssuePicker
CampaignBudgetEditor
```

They may compose owned UI components but should not be moved into the design
system solely because they contain UI.

## New dependency policy

Before adding a UI dependency:

1. Confirm Base UI and native HTML cannot reasonably solve the requirement.
2. Identify the missing behavior.
3. Evaluate licensing and maintenance.
4. Keep the new dependency private inside the owned UI package.
5. Document why it exists.
6. Avoid overlapping component systems.
