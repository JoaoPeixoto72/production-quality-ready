# Anti-Patterns: O Guia Anti-Slop de UI/UX

Este documento define a lista de proibições e vícios comuns gerados por modelos de inteligência artificial na criação de interfaces ("AI Slop"). Qualquer implementação de interface sob a égide do `ui-ux-engine` DEVE respeitar estas regras.

---

## 1. Cores e Iluminação

### ❌ PROIBIDO: O "SaaS Template Indigo"
* **O Erro**: Fundo escuro monótono (`bg-slate-900` ou `bg-zinc-950`) combinado com botões roxos/índigo (`bg-indigo-600`, `bg-violet-600`) e luzes neon desfocadas no fundo (`blur-3xl bg-purple-500/20`).
* **A Correção**: Usar paletas com identidade clara. Se o produto é uma ferramenta profissional, priorizar contrastes neutros refinados com acentos pontuais baseados na função do produto (ex: verde esmeralda para finanças, âmbar para operações/logs, azul cobalto profundo para produtividade técnica).

### ❌ PROIBIDO: Bordas Fluorescentes e Brilhos Excessivos
* **O Erro**: Cartões com `border-indigo-500/50` e sombras externas brilhantes `shadow-[0_0_25px_rgba(99,102,241,0.3)]`.
* **A Correção**: As bordas devem ser semânticas e quase impercetíveis em repouso (`border border-default-200/60` no modo claro, `border border-default-100/30` no modo escuro). Apenas controles ativamente focados podem exibir anéis de foco coloridos.

### ❌ PROIBIDO: Cores Hexadecimais Hardcoded
* **O Erro**: Espalhar `#ffffff`, `#1e293b`, `#3b82f6` ou classes arbitrárias como `text-[#6366f1]` pelos componentes.
* **A Correção**: Toda a cor deve vir dos tokens do HeroUI v3 (`text-foreground`, `text-default-500`, `bg-content1`, `bg-primary`).

---

## 2. Superfícies e Hierarquia (A Síndrome do Card Plano)

### ❌ PROIBIDO: "Cards em Cascata" sem Elevação
* **O Erro**: Criar uma página onde o fundo é cinzento, dentro há um card com `bg-white dark:bg-zinc-900`, dentro dele há outro card com o mesmo fundo, e dentro deste há inputs com o mesmo fundo, diferenciando-os apenas por linhas cinzentas finas.
* **A Correção**: Utilizar rigorosamente as superfícies em camadas:
  1. `background`: O ecrã onde tudo assenta.
  2. `content1`: O painel principal (ex: Card pai ou Sidebar).
  3. `content2`: Agrupamentos internos (ex: subseção de definições).
  4. `content3`: Superfície de controles (inputs, botões de ação secundária).
  5. `content4`: Hover states ou popovers que flutuam acima de tudo.

### ❌ PROIBIDO: Sombras Exageradas em Ferramentas Utilitárias
* **O Erro**: Usar `shadow-2xl` em todos os blocos de uma dashboard de métricas.
* **A Correção**: Interfaces de produtividade usam bordas nítidas de 1px e micro-sombras táteis (`shadow-sm`). Sombras difusas são reservadas unicamente para Overlays flutuantes (Diálogos, Menus e Popovers).

---

## 3. Controles Interativos e Física Tátil

### ❌ PROIBIDO: Botões "Mortos" (Sem Micro-Interação)
* **O Erro**: Um botão que apenas muda ligeiramente de cor no `:hover` e não reage ao clique.
* **A Correção**: Todo o elemento interativo deve ter física tátil:
  ```css
  /* Padrão obrigatório */
  transition: all 200ms cubic-bezier(0, 0, 0.2, 1);
  ```
  No Tailwind: `transition-all duration-200 active:scale-[0.97]`.

### ❌ PROIBIDO: Botões "Pílula" (`rounded-full`) em Ferramentas de Trabalho
* **O Erro**: Botões completamente arredondados tipo cápsula em editores de código, dashboards analíticas ou ferramentas B2B.
* **A Correção**: Usar curvaturas modernas proporcionais:
  - `rounded-medium` (12px / `rounded-xl`) para botões, inputs e diálogos padrão.
  - `rounded-small` (8px / `rounded-lg`) para tabelas compactas e ferramentas de alta densidade.
  - Reservar `rounded-full` exclusivamente para Avatares, Badges de estado e Chips de seleção.

### ❌ PROIBIDO: Esquecer o Estado de Foco de Acessibilidade
* **O Erro**: Remover o outline com `focus:outline-none` sem adicionar um anel de foco visível para navegação por teclado.
* **A Correção**: Todo o componente interativo DEVE incluir:
  `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background`.

---

## 4. Tipografia e Densidade

### ❌ PROIBIDO: Espaço Desperdiçado ("Hero Section Em Todo o Lado")
* **O Erro**: Em ferramentas de gestão ou software profissional, criar títulos gigantescos com `text-5xl` e espaçamentos de `p-16` que obrigam o utilizador a fazer scroll antes de ver os dados.
* **A Correção**: Respeitar a densidade funcional:
  - Título de página: `text-xl` ou `text-2xl` com `font-semibold tracking-tight`.
  - Corpo da aplicação: `text-sm` com `leading-relaxed`.
  - Metadados e tabelas: `text-xs font-medium text-default-500`.

### ❌ PROIBIDO: Texto Secundário com Opacidades Cegas
* **O Erro**: Usar `opacity-60` no texto que causa problemas graves de contraste e legibilidade.
* **A Correção**: Usar a escala semântica:
  - Texto principal: `text-foreground` (contraste máximo).
  - Texto de suporte: `text-default-500` (garantido WCAG AA).
  - Texto de placeholder/desativado: `text-default-300`.

---

## 5. Resumo da Checklist Anti-Slop

Antes de fechar qualquer interface, confirme se:
1. Não existem gradientes roxos decorativos sem justificação de marca.
2. Os cantos dos botões são proporcionais e têm feedback `active:scale-[0.97]`.
3. Os cards não usam a mesma cor do fundo com uma simples borda fina.
4. O Base UI foi utilizado para a lógica de diálogos/menus em vez de `useState` manuais com divs flutuantes sem acessibilidade.
5. Todos os estados (hover, focus, active, disabled) foram explicitamente tratados.
