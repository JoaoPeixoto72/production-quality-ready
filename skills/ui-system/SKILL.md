---
name: ui-system
description: "Build, migrate or audit the design system: OKLCH tokens, 4 elevations, data-ui contract, @project/ui boundary, executable audit_ui.py. CSS core is framework-agnostic; React components optional. Use for new app/page, DS component, migration."
contract: CONTRACTS.md
argument-hint: "[create | migrate | audit | review | extend | theme | profile] [options]"
platforms: [web, desktop]
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---

# ui-system

Build, migrate and audit the project's design system. Unlike the audit
owners, this skill **writes code** in create/migrate/extend/theme modes;
in audit mode it only reports.

The architecture is strictly unidirectional:

```text
Application (Pages / Views / Routes)
    ↓
@project/ui (own components package or module)
    ↓
Base UI (@base-ui/react v1.8.0) used privately for behaviour, focus and a11y
    ↓
Semantic Tokens (OKLCH), 4 Elevation Layers and Swappable Themes
```

> [!IMPORTANT]
> **Rigid Architectural Boundary**: Base UI (`@base-ui/react`) is an
> internal, private implementation detail. Application code NEVER imports
> Base UI, Radix or HeroUI directly. The application consumes exclusively
> the `@project/ui` package or module.

## Boundary with design-pro (bilateral pair, POLICY §1.2)

This owner is an **instrument**, not the accessibility rule.
`scripts/audit_ui.py` computes ΔL OKLCH — a contrast candidate that feeds
the **design-pro WCAG rule**. No a11y gate closes here; `design-pro`
reads the ΔL value and decides the verdict against WCAG 2.2 SC
1.4.3/1.4.11. See `CONTRACTS.md §4.5` (mechanical authority per check).

---

## 1. Design principles and goals

1. **AI Slop eradication**: Bans generic purple gradients, monotone
   slate backgrounds, default AI typography (Inter, Roboto) and nested
   cards without real semantic elevation.
2. **Layered surfaces (4 elevation levels)**: Deliberate 3D depth using
   `--content1` through `--content4` on the `--background` base.
3. **Tactile physics on every control**:
   - `active:scale-[0.97]` and the boolean selector
     `[data-pressed]:not(:disabled, [data-disabled])` covering pointer,
     touch and keyboard.
   - Mandatory sharp focus rings via `outline` with `outline-offset`
     (supports High Contrast Mode / Forced Colors).
4. **Stable DOM contract (`data-ui`)**:
   - Components expose public semantic attributes (`data-ui="button"`,
     `data-ui="dialog-popup"`, `data-ui="field"`).
   - Lets you swap the visual theme entirely via CSS without touching a
     single line of React code.
5. **Autonomy and offline privacy**:
   - Local typography and tokens with no CDN dependency. Font binaries
     are not embedded in the skill build; the project supplies the files
     or the app downloads them dynamically at runtime.
   - `isolation: isolate` mandatory on the app root to prevent z-index
     stacking leakage.

---

## 2. Operating modes

- **Create**: Initialize a new app, page or component by copying the
  base files from `assets/` (`ui.config.json`, tokens and core CSS from
  `assets/css/`; React components from `packs/react-components/` only
  when the project is React) into the project's UI directory (e.g.
  `src/ui/`). Non-React stacks (hono/jsx, Svelte, Vue, vanilla, Tauri
  without React) take tokens + core + themes and write their own
  components against the `data-ui` contract.
- **Migrate**: Move an existing app progressively to `@project/ui` in
  concentric layers.
- **Audit**: Inspect conformance, focus rings, imports and OKLCH
  contrast with the deterministic script.
- **Review**: Assess completed work and certify conformance before
  handoff.
- **Extend**: Add new components to the public `@project/ui` library.
- **Theme**: Switch or create new visual themes (`neutral`, `heroui`,
  `studio`, `editorial`).
- **Profile**: Apply the base profile (`assets/ui.config.json`) or a
  project-supplied one under `profiles/<name>/`.

When multiple modes apply, follow the canonical order:

```text
Audit → Plan → Implement or Migrate → Review
```

---

## 3. Progressive reference disclosure

Consult the modular manuals as needed to keep context small:

- **For component creation and architecture**:
  - [references/architecture.md](references/architecture.md): boundary
    of the `@project/ui` package and import policies.
  - [references/component-strategy.md](references/component-strategy.md):
    canonical Base UI v1.8.0 matrix.
  - [references/anti-patterns.md](references/anti-patterns.md):
    categorical bans and anti-slop catalog.
- **For design, tokens and themes**:
  - [references/design-language.md](references/design-language.md):
    OKLCH colors, elevation and tactile physics.
  - [references/upstream.md](references/upstream.md): global resets, iOS
    Safari fallback and typography.
- **For migrations and quality assurance**:
  - [references/migration-playbook.md](references/migration-playbook.md):
    non-destructive migration in concentric layers.
  - [references/quality-standard.md](references/quality-standard.md):
    deterministic acceptance checklist. Interaction and Accessibility
    sections carry an "Instrument — see design-pro" header (points at
    the WCAG rule).
  - [references/workflows.md](references/workflows.md): detailed
    execution guides.

---

## 4. Bundled resources (`assets/`)

The skill ships code ready to inject into the project:

```text
assets/
├── ui.config.json                    # Canonical config of themes and paths
├── css/
│   ├── index.css                     # Entry: @layer ui.reset, ui.tokens, ui.core, ui.theme
│   ├── tokens.css                    # OKLCH invariant primitives, 4px spacing
│   ├── core.css                      # data-ui slot mechanics, outline focus, resets
│   ├── tailwind-bridge.css           # Inline @theme bridge for Tailwind CSS v4
│   └── themes/
│       ├── neutral.css               # Agnostic zinc/slate default (sober SaaS)
│       ├── heroui.css                # Modern SaaS (4 surfaces content1-content4)
│       ├── studio.css                # Dark industrial / amber workstation
│       └── editorial.css             # Expressive editorial with serif
packs/
└── react-components/                 # Optional React pack (HeroUI parity, Level 2)
```

> [!IMPORTANT]
> **The count is verifiable, and is meant to be verified before writing a
> new component:** `ls packs/react-components/*.tsx | wc -l`. If the number
> differs from what a caller expected, this list is stale and a hidden
> component becomes a hand-rewritten one.

---

## 5. Profiles (`profiles/`)

The skill ships the **base profile** (`assets/ui.config.json`: neutral
theme, offline fonts, no CDN). A project with specific constraints
(Tauri offline suite, pure-black canvas, tabular numerics…) adds its own
`profiles/<name>/{ui.config.json, profile.md, assets/}` and applies it:

```bash
# base profile, CSS only (any stack)
python scripts/apply_profile.py --target .
# base profile + React component pack
python scripts/apply_profile.py --target . --with-react
# project profile
python scripts/apply_profile.py <name> --target .
```

Paths are relative to this skill's folder (the directory holding this
`SKILL.md`), wherever the host installed the plugin.

---

## 6. Deterministic quality audit (`scripts/audit_ui.py`)

Before finishing any task, run the strict auditor:

```bash
python scripts/audit_ui.py <target-dir> --strict
```

To validate with a specific profile:

```bash
python scripts/audit_ui.py <target-dir> --profile <name> --strict
```

The auditor validates and blocks (`error`):

1. **Architectural boundary**: direct imports of `@base-ui/react`,
   `@radix-ui/*` or `@heroui/*` outside the UI package folder.
2. **Legacy package name**: use of `@base-ui-components/react`.
3. **Invalid boolean selectors**: `[data-pressed="true"]` instead of
   `[data-pressed]`.
4. **`color-mix()` sums**: total percentages ≠ 100 %.
5. **OKLCH luminance heuristic**: semantic pairs with $|\Delta L| < 0.40$
   (and $\Delta L < 0.30$ on primary text). **Instrument** — the a11y
   verdict closes in `design-pro` against WCAG 2.2 SC 1.4.3/1.4.11.
6. **Remote fonts and CDNs**: offline-policy violations in local/Tauri
   environments.
7. **Generic AI fonts**: unjustified use of Inter or Roboto.
8. **Focus rings**: use of `box-shadow` on `:focus-visible` instead of
   `outline`.
9. **Motion accessibility**: transitions without `prefers-reduced-motion`
   coverage.
10. **Unstyled component**: a component in the UI package whose
    `data-ui` slots are **all** unstyled — it renders with no styling. A
    single loose slot is only a warning (`unstyled-slot`).

## This owner does NOT

- Close a11y verdicts — that's `design-pro` (bilateral pair).
- Write generic UX outside the DS — that's `design-pro`.
- Decide bundle budget — that is `code-review` (`perf.*`).

## Accepted instruments

See `instruments.yaml`. The canonical producer of the checks above is
`ui-system::audit_ui.py`. Without it, `NOT_VERIFIED/missing-producer`.
