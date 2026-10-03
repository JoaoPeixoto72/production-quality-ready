# Migration playbook: smooth and non-destructive

## Contents

- Golden rule: non-destructive migration
- Phase 0: audit and inventory
- Phase 1: token foundation (no breakage)
- Phase 2: atomic controls
- Phase 3: surfaces and layout shell
- Phase 4: overlays and complex components
- Phase 5: cleanup and final audit

The deterministic procedure to move an existing app (generic design, raw
Tailwind, Radix, old Shadcn or MUI) onto **Base UI + HeroUI v3 CSS**, without
stopping it from working or building.

## Golden rule: non-destructive migration

> [!IMPORTANT]
> A migration **never** deletes old classes or uninstalls packages in its first
> phase. The app stays buildable and testable at every step. It moves in
> **concentric layers**: token foundation → atomic controls → layout surfaces →
> overlays → final cleanup.

## Phase 0: audit and inventory

Before touching code, run the automated inspection on the target app:

```bash
python .claude/skills/ui-system/scripts/audit_ui.py .
```

It finds:
1. Every UI library in `package.json` (`@radix-ui/*`, `@headlessui/*`, `antd`, `@mui/*`).
2. Every loose hex colour (`#1e293b`, `#3b82f6`, …).
3. Arbitrary Tailwind classes (`bg-[#...]`, `text-[13px]`).

Keep the checklist in the ignored work folder, `.work/ui-migration.md`:
```markdown
# UI migration checklist

- [ ] Phase 1: token foundation injected and building
- [ ] Phase 2: buttons and inputs migrated
- [ ] Phase 3: layout shell and surfaces (content1/content2)
- [ ] Phase 4: dialogs and menus on Base UI
- [ ] Phase 5: old dependencies removed, audit clean
```

## Phase 1: token foundation (no breakage)

1. Install the essentials:
   ```bash
   npm install @base-ui/react clsx tailwind-merge class-variance-authority lucide-react
   ```
2. Import `tokens.css` at the top of the global styles (`src/globals.css` or `src/index.css`).
3. With Tailwind, extend `tailwind.config.ts` with the semantic keys (`content1`..`content4`, `primary`, …).
4. **Required check**: `npm run build` or the project's linter. Nothing breaks: the old classes are untouched.

## Phase 2: atomic controls

### 1. Buttons
- Map old styles onto the HeroUI v3 variants:
  - `<button className="bg-blue-600 hover:bg-blue-700 text-white rounded px-4 py-2">`
    → `<Button variant="solid" color="primary">`
  - `<button className="border border-gray-300 text-gray-700 rounded px-3 py-1">`
    → `<Button variant="bordered">`
  - `<button className="bg-gray-100 hover:bg-gray-200 text-gray-800">`
    → `<Button variant="flat">`

### 2. Inputs and text fields
- Replace hard-bordered native inputs with the `components/ui/input.tsx` blueprint (Base UI Field): tactile focus, `bg-content3` surfaces.

## Phase 3: surfaces and layout shell

This phase removes the flat look at once:

1. **Base canvas**: in the root container (`App.tsx`, `layout.tsx` or `<body>`), replace `bg-slate-900`, `bg-gray-900` or `bg-gray-50` with `bg-background text-foreground`.
2. **Primary surfaces (`content1`)**: navbar, sidebar and structural panels get `bg-content1 border-r border-default-200/50`.
3. **Secondary surfaces (`content2`)**: lists, tables and inner cards get `bg-content2 rounded-large border border-default-200/40`.

## Phase 4: overlays and complex components

1. **Dialogs**: replace hand-made `isOpen && <div className="fixed...">` with Base UI's `Dialog`; backdrop `backdrop-blur-md bg-black/40`.
2. **Dropdowns and menus**: Base UI's Menu, with automatic positioning and no overflow or z-index breakage.

## Phase 5: cleanup and final audit

1. Run the script again:
   ```bash
   python .claude/skills/ui-system/scripts/audit_ui.py .
   ```
2. Confirm that arbitrary hex colours dropped sharply or to zero, and no old UI library import is orphaned.
3. Remove any old package no file imports any more:
   ```bash
   npm uninstall @radix-ui/react-dialog
   ```
4. Delete `.work/ui-migration.md` once the user confirms.
