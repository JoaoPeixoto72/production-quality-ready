## Base UI

Package: `@base-ui/react`.

Fontes oficiais:

- Docs: https://base-ui.com/
- Índice para LLMs: https://base-ui.com/llms.txt
- Qualquer página em Markdown: acrescentar `.md` ao URL
- Repositório: https://github.com/mui/base-ui
- Releases: https://base-ui.com/react/overview/releases

## Setup obrigatório

1. `isolation: isolate` no root da aplicação.
2. Para iOS Safari, seguir o padrão documentado do quick start: backdrop
   `position: fixed` por omissão e `position: absolute` apenas no fallback
   com `body { position: relative; }`.
3. O backdrop tem de ser filho directo do Portal, nunca dentro do viewport.

## Fontes

Esta skill não distribui binários de fontes. Se um profile recomendar uma
família específica, o projecto consumidor tem de fornecer os ficheiros,
declarações `@font-face` e licenças correspondentes.

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
