# Anti-patterns: the UI anti-slop guide

What generated interfaces ("AI slop") tend to do wrong. Any interface built
under `ui-system` MUST respect these rules.

## 1. Colour and light

### ❌ The "SaaS template indigo"
* **Mistake**: a flat dark background (`bg-slate-900`, `bg-zinc-950`) with purple/indigo buttons (`bg-indigo-600`, `bg-violet-600`) and blurred neon glows (`blur-3xl bg-purple-500/20`).
* **Fix**: a palette with identity. A professional tool takes refined neutral contrast with accents tied to its function (emerald for finance, amber for operations/logs, deep cobalt for technical productivity).

### ❌ Fluorescent borders and excessive glow
* **Mistake**: cards with `border-indigo-500/50` and glowing outer shadows `shadow-[0_0_25px_rgba(99,102,241,0.3)]`.
* **Fix**: semantic borders, near-invisible at rest (`border-default-200/60` light, `border-default-100/30` dark). Only actively focused controls show coloured rings.

### ❌ Hard-coded hex colours
* **Mistake**: `#ffffff`, `#1e293b`, `#3b82f6` or `text-[#6366f1]` scattered through components.
* **Fix**: every colour comes from the tokens (`text-foreground`, `text-default-500`, `bg-content1`, `bg-primary`).

## 2. Surfaces and hierarchy (flat-card syndrome)

### ❌ Cascading cards without elevation
* **Mistake**: grey page, a `bg-white dark:bg-zinc-900` card, another card of the same colour inside, inputs of the same colour inside that, told apart only by thin grey lines.
* **Fix**: layered surfaces:
  1. `background`: the screen everything sits on.
  2. `content1`: the main panel (parent card, sidebar).
  3. `content2`: inner groupings (a settings subsection).
  4. `content3`: control surfaces (inputs, secondary action buttons).
  5. `content4`: hover states and popovers floating above everything.

### ❌ Heavy shadows in utility tools
* **Mistake**: `shadow-2xl` on every block of a metrics dashboard.
* **Fix**: productivity UIs use crisp 1px borders and tactile micro-shadows (`shadow-sm`); diffuse shadows are for floating overlays only (dialogs, menus, popovers).

## 3. Interactive controls and tactile physics

### ❌ Dead buttons (no micro-interaction)
* **Mistake**: a button that only shifts colour on `:hover` and does not react to the click.
* **Fix**: every interactive element has tactile physics:
  ```css
  transition: all 200ms cubic-bezier(0, 0, 0.2, 1);
  ```
  In Tailwind: `transition-all duration-200 active:scale-[0.97]`.

### ❌ Pill buttons (`rounded-full`) in work tools
* **Mistake**: capsule buttons in code editors, analytics dashboards or B2B tools.
* **Fix**: proportional radii:
  - `rounded-medium` (12px / `rounded-xl`) for standard buttons, inputs and dialogs;
  - `rounded-small` (8px / `rounded-lg`) for compact tables and dense tools;
  - `rounded-full` only for avatars, status badges and selection chips.

### ❌ Forgetting the focus state
* **Mistake**: `focus:outline-none` with no visible focus ring for keyboard navigation.
* **Fix**: every interactive component includes
  `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background`.

## 4. Typography and density

### ❌ Wasted space (hero sections everywhere)
* **Mistake**: in management or professional software, `text-5xl` titles and `p-16` spacing that make the user scroll before seeing data.
* **Fix**: functional density:
  - page title: `text-xl` or `text-2xl`, `font-semibold tracking-tight`;
  - app body: `text-sm`, `leading-relaxed`;
  - metadata and tables: `text-xs font-medium text-default-500`.

### ❌ Secondary text by blind opacity
* **Mistake**: `opacity-60` on text, breaking contrast and legibility.
* **Fix**: the semantic scale:
  - main text: `text-foreground` (maximum contrast);
  - supporting text: `text-default-500` (WCAG AA);
  - placeholder/disabled text: `text-default-300`.

## 5. Anti-slop checklist

Before closing any interface, confirm that:
1. There are no decorative purple gradients without a brand reason.
2. Button corners are proportional and give `active:scale-[0.97]` feedback.
3. Cards do not use the background colour with a thin border.
4. Base UI drives dialogs/menus, not hand-made `useState` with floating divs.
5. Every state (hover, focus, active, disabled) is handled explicitly.
