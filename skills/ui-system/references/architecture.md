# Architecture

## Purpose

The project owns its public component API, visual language, tokens, CSS,
documentation, and release process.

Base UI is a private behavior implementation used inside the owned UI package.

## Default dependency direction

```text
Application
    ↓
@project/ui
    ├── native HTML components
    ├── project patterns
    └── Base UI-backed components
            ↓
       @base-ui/react
```

Dependencies must point downward. Base UI must never import project components,
and application code must not bypass `@project/ui`.

## Recommended packages

Adapt these names to the repository:

```text
packages/
├── ui-tokens/
├── ui-css/
├── ui-react/
└── ui-icons/
```

A single package is acceptable for small projects:

```text
src/ui/
├── components/
├── styles/
├── tokens/
└── index.ts
```

Do not restructure an existing repository merely to match this example.

## Responsibilities

### UI tokens

Owns:

- primitive values;
- semantic values;
- component aliases;
- light and dark modes;
- theme values.

Does not own React behavior.

### UI CSS

Owns:

- reset or normalization, if needed;
- core functional component CSS;
- theme CSS.

Does not own application-specific layout.

### UI React

Owns:

- public component API;
- native components;
- Base UI wrappers;
- stable slots;
- variants;
- component defaults;
- component-level accessibility integration.

Does not own product-specific business logic.

### Application

Owns:

- domain components;
- page composition;
- data loading;
- routing;
- business rules;
- application-specific content.

## Import policy

Allowed in application code:

```tsx
import { Button, Dialog } from "@project/ui";
```

Allowed inside the UI package:

```tsx
import { Dialog as BaseDialog } from "@base-ui/react/dialog";
```

Not allowed in application code:

```tsx
import { Dialog } from "@base-ui/react/dialog";
```

## Cascade layers

All system CSS lives in the `ui.*` layers. Normal declarations inside a
layer lose to unlayered declarations regardless of specificity, so any
application stylesheet written outside a layer overrides the design
system. Treat that as the documented escape hatch, and keep application
CSS layered when the intent is to cooperate rather than override.

In Tailwind v4 projects the layer order must be declared once, before
any import, because Tailwind declares its own layers when imported:

    @layer theme, base, ui.reset, ui.tokens, ui.core, ui.theme,
           components, utilities;

Use the explicit `index.tailwind.css` entry point when the repository
uses Tailwind v4. It declares the shared order and imports
`tailwind-bridge.css` after `@import "tailwindcss"`, preventing
Tailwind's default font variables from winning over the bridge.

## Public API stability

The application depends on project semantics, not upstream semantics.

Good:

```tsx
<Button variant="danger">Delete</Button>
```

Avoid:

```tsx
<Button className="bg-red-600 rounded-xl shadow-md">
  Delete
</Button>
```

The first can change through theme CSS. The second spreads visual decisions
through application code.

## Base UI upgrade policy

Treat Base UI upgrades as internal infrastructure changes:

1. Review release notes.
2. Update in a dedicated branch.
3. Run component tests.
4. Run keyboard and accessibility checks.
5. Review visual screenshots.
6. Confirm public project APIs have not changed.
7. Release the owned UI package according to its own versioning policy.

Do not automatically expose new upstream props through the public API.

## Escape hatches

Allow controlled customization through:

- `className`;
- `style` when necessary;
- stable slot attributes;
- documented render or composition APIs;
- CSS custom properties;
- semantic variants.

Do not expose every upstream option merely because it exists.
