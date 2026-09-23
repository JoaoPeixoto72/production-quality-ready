# Component Strategy

## Contents

- Escolher o nível de implementação
- Componentes verificados no Base UI
- Não existem no Base UI
- Preferir Base UI mesmo onde o HTML parece suficiente
- Sempre Base UI
- Como confirmar a API antes de escrever código
- Component contract
- Variant discipline
- Size discipline
- Compound components
- Domain components
- New dependency policy

## Escolher o nível de implementação

Usar o nível mais baixo suficiente:

1. HTML nativo.
2. Componente próprio existente.
3. Padrão próprio existente.
4. Base UI encapsulado privadamente.
5. Novo primitivo próprio, só quando necessário.
6. Componente de domínio da aplicação.

## Componentes verificados no Base UI

Lista verificada contra https://base-ui.com/llms.txt (v1.8.0). Sempre
reconfirmar contra a versão instalada antes de implementar.

Overlays e navegação: Dialog, Alert Dialog, Drawer, Popover, Tooltip,
Preview Card, Menu, Menubar, Context Menu, Navigation Menu, Toolbar,
Tabs, Toast.

Selecção e entrada: Select, Combobox, Autocomplete, Input, Number Field,
OTP Field, Checkbox, Checkbox Group, Radio, Switch, Toggle,
Toggle Group, Slider.

Formulários: Field, Fieldset, Form.

Estrutura e feedback: Accordion, Collapsible, Scroll Area, Separator,
Progress, Meter, Avatar, Button.

Utilitários: CSP Provider, Direction Provider, mergeProps, useRender.

## Não existem no Base UI

Estes têm de ser próprios, sobre HTML nativo:

Badge, Card/Surface, Skeleton, Spinner, Table/DataTable, Breadcrumb,
Pagination, Empty State, Stack, Inline, Grid, Container, Heading, Text,
Link, Textarea.

## Preferir Base UI mesmo onde o HTML parece suficiente

| Componente | Porque não ficar no nativo |
|---|---|
| Field | Faz o labelling e a validação, e a relação label/erro/descrição |
| Form | Consolida o tratamento de erros do formulário |
| Fieldset | Legend estilizável, que é notoriamente difícil em CSS |
| Button | Renderizável noutra tag e focável quando disabled |
| Input | Integra com Field e Form |
| Separator | Semântica correcta para leitores de ecrã |
| Progress, Meter | Semântica ARIA e valores |
| Avatar | Estados de fallback de imagem |

Um `<button>` nativo continua correcto para acções isoladas fora de
formulários. Um `<input>` solto num formulário real quase nunca é a
escolha certa: perde-se a relação com label, descrição e erro.

## Sempre Base UI

Nunca implementar à mão: focus trap, dismissal, posicionamento de
popups, navegação por teclado em colecções, anúncios de toast, gestos
de swipe, ou virtual focus. É trabalho não diferenciado e difícil de
acertar.

## Como confirmar a API antes de escrever código

Ordem obrigatória:

1. Tipos e código do package instalado, e o lockfile.
2. `https://base-ui.com/llms.txt` para o índice de componentes.
3. A página de docs do componente com o sufixo `.md`
   (ex: `https://base-ui.com/react/components/select.md`), que devolve
   Markdown pronto a ler.
4. Nunca gerar props de memória.

Nota do próprio `llms.txt`: os exemplos de Tailwind estão escritos para
v4; se o `package.json` usar v3, converter.

O quick start pede explicitamente que a documentação do Base UI seja
tratada como autoritária em conflito com conhecimento prévio, e cada
página tem link "View as Markdown". Isto reforça a regra acima: nunca
gerar props de memória — abrir a versão Markdown da página do
componente e ler o contrato.

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
