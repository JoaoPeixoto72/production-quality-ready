## Base UI

Package: `@base-ui/react`.

Official sources:

- Docs: https://base-ui.com/
- Index for LLMs: https://base-ui.com/llms.txt
- Any page as Markdown: append `.md` to the URL
- Repository: https://github.com/mui/base-ui
- Releases: https://base-ui.com/react/overview/releases

## Required setup

1. `isolation: isolate` on the app root.
2. For iOS Safari, the quick start's documented pattern: backdrop
   `position: fixed` by default and `position: absolute` only in the fallback
   with `body { position: relative; }`.
3. The backdrop is a direct child of the Portal, never inside the viewport.

## Fonts

This skill ships no font binaries. If a profile recommends a family, the
consuming project provides the files, the `@font-face` declarations and the
licences.

## Base UI usage policy

Level 2 uses Base UI as a runtime dependency inside the owned UI package.

Do not copy the Base UI source merely to avoid a dependency unless the user
explicitly chooses a fork or vendoring strategy.

Do not expose Base UI imports to applications.

## shadcn

shadcn is not required by this architecture.

It may be studied for source distribution, registries, wrapper ergonomics, and
composition examples.

Do not add it automatically and do not copy its visual defaults into the owned
system.

## HeroUI

HeroUI may be used as visual research when requested, but it is not the default
foundation.

## Radix

Radix is not used when Base UI already meets the requirement. Avoid running two
overlapping primitive systems without a documented reason.

## Source-use policy

When adapting external source:

1. Use the actual repository, not model memory.
2. Pin an exact version or commit.
3. Confirm the license.
4. Preserve required notices.
5. Record the source and modifications.
6. Avoid copying premium or separately licensed assets.
7. Port relevant tests when code is substantially derived.
