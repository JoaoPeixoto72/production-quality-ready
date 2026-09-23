# Workflows

## Contents

- Create a new application or page
- Migrate an existing application
- Extend the component system
- Create or modify a theme

## Create a new application or page

### 1. Inspect

Identify:

- framework;
- package manager;
- project structure;
- existing design-system package;
- styling approach;
- test setup;
- product context;
- routes and data requirements.

### 2. Establish direction

Write:

```text
Product:
Audience:
Primary job:
Usage frequency:
Density:
Theme:
Characteristic idea:
Required pages:
Required states:
```

If product context is genuinely unavailable and strongly affects the result,
ask one focused question or propose an explicit working assumption.

### 3. Inventory required UI

Classify each element:

```text
Existing owned component
Native component
Base UI-backed component
Owned pattern
Domain component
```

Do not create page-local substitutes for owned components.

### 4. Build foundations first

When absent, establish:

1. tokens;
2. core CSS;
3. active theme;
4. typography;
5. layout primitives;
6. form foundations;
7. overlays;
8. page composition.

Do not build an entire theoretical library before implementing the required
product.

### 5. Implement with real content

Content length and meaning influence design. Include:

- realistic names;
- realistic labels;
- realistic data ranges;
- long-content examples;
- empty and error states.

### 6. Validate

Test:

- keyboard;
- narrow viewport;
- wide viewport;
- long content;
- zero data;
- errors;
- loading;
- reduced motion;
- focus visibility.

---

## Migrate an existing application

### 1. Create an inventory

Record:

- direct external UI imports;
- components and duplicate implementations;
- colors and hardcoded values;
- typography;
- spacing;
- radius;
- shadows;
- breakpoints;
- CSS strategy;
- routes;
- forms;
- overlays;
- tests;
- analytics and test selectors.

Use `scripts/audit_ui.py` as evidence, not as the entire audit.

### 2. Capture behavioral baselines

Before visual changes, identify:

- routes and navigation;
- form payloads;
- validation messages;
- loading and error behavior;
- focus behavior;
- keyboard behavior;
- analytics;
- screenshots;
- current automated tests.

### 3. Map semantics

Create a migration map:

```text
LegacyButton → @project/ui Button
LegacyModal → @project/ui Dialog
#2563eb used for actions → --accent
24px section gap → --section-gap
```

Map by purpose, not merely by similar visual value.

### 4. Introduce foundations

Add or normalize:

- UI package boundary;
- tokens;
- core CSS;
- target theme;
- owned exports.

Avoid changing all application pages at once.

### 5. Add adapters

When a legacy API has many consumers, create a temporary adapter:

```text
Legacy API
    ↓
compatibility adapter
    ↓
owned component
```

Mark adapters as transitional and track usage.

### 6. Migrate incrementally

Suggested sequence:

1. buttons, text, labels, inputs;
2. badges, alerts, surfaces;
3. fields and forms;
4. dialogs, popovers, tooltips;
5. selects, menus, comboboxes;
6. navigation;
7. tables and dense patterns;
8. application shells;
9. route-by-route cleanup.

### 7. Remove legacy code safely

Before removal:

- search for imports;
- search dynamic usage;
- run type checking;
- run tests;
- build production;
- inspect critical routes;
- confirm no adapter usage remains.

---

## Extend the component system

### 1. Prove reuse

Confirm the concept is reusable across more than one immediate call site or is
foundational enough to warrant central ownership.

### 2. Write the contract

Use the contract in `component-strategy.md`.

### 3. Choose the foundation

Use:

- native HTML when sufficient;
- Base UI internally for complex behavior;
- a new dependency only with explicit justification.

### 4. Implement all relevant states

Do not stop at the default screenshot.

### 5. Add exports and documentation

Ensure application code imports only the owned package.

### 6. Test independently and in context

A component may work alone but fail inside:

- forms;
- portals;
- dialogs;
- scroll containers;
- mobile layouts;
- dark themes;
- nested overlays.

---

## Create or modify a theme

### 1. Preserve semantic contracts

Do not rename public variants merely to reflect a new visual style.

### 2. Establish the theme concept

Define:

- personality;
- typography;
- palette;
- geometry;
- surface behavior;
- density;
- border philosophy;
- shadow philosophy;
- motion philosophy;
- image and icon treatment.

### 3. Change tokens first

Prefer theme-level custom properties.

### 4. Add structural theme CSS when needed

Tokens alone cannot express every design. Themes may style stable `data-ui`
slots differently.

### 5. Test representative components

At minimum:

- button;
- field;
- select;
- dialog;
- menu;
- tabs;
- alert;
- table or dense data view;
- empty state;
- full page.

### 6. Test contrast and states

A theme is incomplete if only its default state looks correct.
