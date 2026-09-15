# Playbook de Migração: Transição Suave e Não-Destrutiva

Este manual define o procedimento determinístico para transformar uma aplicação existente (com design genérico, Tailwind cru, Radix, Shadcn antigo ou MUI) na arquitetura **Base UI + HeroUI v3 CSS**, sem interromper o funcionamento nem quebrar a compilação do projeto.

---

## Regra de Ouro: Migração Não-Destrutiva

> [!IMPORTANT]
> Uma migração **nunca** apaga classes antigas ou desinstala pacotes na primeira fase. A aplicação tem de se manter compilável e testável a cada passo. A transição faz-se por **camadas concêntricas**: Fundação de Tokens → Controles Atómicos → Superfícies de Layout → Overlays → Limpeza Final.

---

## Fase 0: Auditoria e Inventário

Antes de modificar código, o agente executa a inspeção automatizada da app de destino:

```bash
python .claude/skills/ui-system/scripts/audit_ui.py .
```

O script identifica:
1. Todas as bibliotecas de UI instaladas no `package.json` (ex: `@radix-ui/*`, `@headlessui/*`, `antd`, `@mui/*`).
2. Todas as ocorrências de cores hexadecimais soltas (`#1e293b`, `#3b82f6`, etc.).
3. Classes arbitrárias de Tailwind (`bg-[#...]`, `text-[13px]`).

O agente cria no projeto um ficheiro de controlo `UI_MIGRATION_PLAN.md` com a checklist gerada:
```markdown
# Checklist de Migração de UI

- [ ] Fase 1: Fundação de Tokens injetada e compilando
- [ ] Fase 2: Botões e Inputs migrados
- [ ] Fase 3: Layout Shell e Superfícies (content1/content2)
- [ ] Fase 4: Modais e Menus migrados para Base UI
- [ ] Fase 5: Dependências antigas removidas e auditoria limpa
```

---

## Fase 1: Fundação de Tokens (Sem Quebras)

1. Instalar as dependências essenciais:
   ```bash
   npm install @base-ui/react clsx tailwind-merge class-variance-authority lucide-react
   ```
2. Adicionar o ficheiro `tokens.css` aos estilos globais do projeto:
   - Se existir `src/globals.css` ou `src/index.css`, importar o `tokens.css` no topo.
3. Se o projeto usar Tailwind, estender o `tailwind.config.ts` com as novas chaves semânticas (`content1`..`content4`, `primary`, etc.).
4. **Verificação obrigatória**: Rodar `npm run build` ou o linter do projeto. Nada deve quebrar porque as classes antigas continuam intactas.

---

## Fase 2: Migração dos Controles Atómicos

Substituir elementos interativos mais comuns:

### 1. Botões
- Mapeamento direto de estilos antigos para as variantes do HeroUI v3:
  - `<button className="bg-blue-600 hover:bg-blue-700 text-white rounded px-4 py-2">`
    → `<Button variant="solid" color="primary">`
  - `<button className="border border-gray-300 text-gray-700 rounded px-3 py-1">`
    → `<Button variant="bordered">`
  - `<button className="bg-gray-100 hover:bg-gray-200 text-gray-800">`
    → `<Button variant="flat">`

### 2. Inputs e Campos de Texto
- Substituir inputs nativos com bordas duras pelo blueprint `components/ui/input.tsx` (Base UI Field), garantindo foco tátil e superfícies `bg-content3`.

---

## Fase 3: Superfícies e Layout Shell

Esta fase transforma imediatamente a perceção visual da aplicação eliminando o visual plano:

1. **Tela Base**:
   - Procurar o contêiner raiz (geralmente em `App.tsx`, `layout.tsx` ou `<body>`).
   - Substituir `bg-slate-900`, `bg-gray-900` ou `bg-gray-50` por `bg-background text-foreground`.

2. **Superfícies Primárias (`content1`)**:
   - Identificar a Navbar, Sidebar e painéis estruturais.
   - Aplicar `bg-content1 border-r border-default-200/50`.

3. **Superfícies Secundárias (`content2`)**:
   - Identificar listas, tabelas e cartões internos.
   - Aplicar `bg-content2 rounded-large border border-default-200/40`.

---

## Fase 4: Overlays e Componentes Complexos

Migração de componentes com estado e acessibilidade:

1. **Modais / Diálogos**:
   - Substituir implementações manuais de `isOpen && <div className="fixed...">` pelo componente `Dialog` do Base UI.
   - Adicionar o backdrop com `backdrop-blur-md bg-black/40`.

2. **Dropdowns e Menus**:
   - Migrar para o Menu do Base UI, aproveitando o posicionamento automático sem risco de overflow ou quebra de z-index.

---

## Fase 5: Limpeza e Auditoria Final

1. Reexecutar o script:
   ```bash
   python .claude/skills/ui-system/scripts/audit_ui.py .
   ```
2. Confirmar que:
   - Cores hexadecimais arbitrárias caíram drasticamente ou foram a zero.
   - Não há imports órfãos de bibliotecas antigas de UI.
3. Se algum pacote antigo (ex: `@radix-ui/react-dialog`) já não tiver qualquer ficheiro a importá-lo, removê-lo:
   ```bash
   npm uninstall @radix-ui/react-dialog
   ```
4. Eliminar o ficheiro de controlo `UI_MIGRATION_PLAN.md` após confirmação do utilizador.
