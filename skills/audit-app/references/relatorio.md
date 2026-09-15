# Relatório

**Aviso — hierarquia.** Formato de saída do `audit-app`. Tradução operacional
das regras de agregação e verdict do `CONTRACTS.md` (§7 gates, §4.3 cobertura)
para a estrutura de um relatório humano. Autoritativo é o `CONTRACTS.md`.

Traduções entre este ficheiro e o `CONTRACTS.md`:

- "Módulo" (aqui) = "owner" (`CONTRACTS.md`).
- "Obrigação" (aqui) = "check canónico" (§7.4).
- "Gate crítico" (aqui) = "check com predicado num gate declarativo" (§7.1).
- Fracção `X/Y` na cobertura = §4.3.1 (obrigatória).

Primária em todos os módulos. O relatório cobre **os módulos pedidos**, não
todos os que existem.

Índice: [Abertura](#abertura-obrigatória) · [Tabela de obrigações](#tabela-de-obrigações-obrigatória) ·
[Findings](#findings) · [Prioridades](#prioridades) · [Alertas](#alertas-por-confirmar) ·
[Hipóteses](#hipóteses) · [Fecho](#fecho)

## Abertura obrigatória

```markdown
## 1. Resultado
<módulo>: Produto: PASS | CONCERNS | FAIL · Cobertura: COMPLETE | PARTIAL | BLOCKED (X/Y)
— uma frase de justificação.
(A fracção é dos gates críticos resolvidos, e é obrigatória: `BLOCKED (0/8)`
não é a mesma auditoria que `BLOCKED (7/8)`.)
(Um par por módulo executado. Global só em `full`, pelas regras de agregação
do SKILL.md.)

## 2. Âmbito
Pedido: "<pedido do utilizador>"
Módulos executados: <lista>
Referências auxiliares abertas: <lista, ou nenhuma>
Módulos não executados: <lista, com uma razão>
Interpretação: <só se o pedido era ambíguo — a escolha feita, numa frase>

## 3. Evidência
Contrato: versão <X.Y.Z> · SHA-256 <digest>   (copiados do validate_skill.py)
Commit: <sha curto>  Árvore no início (t0): limpa | suja (<n> ficheiros)
Árvore no fim (t1): igual | ALTERADA (<caminhos> — e o que isso invalidou)
Ambiente: <SO, versões lidas dos lockfiles>
Capacidade: INTERACTIVE | ASSISTED | STATIC
Comandos: <comando — cwd — exit code>
  (O código copia-se do terminal no momento em que o comando correu, nunca de
  memória nem do que se espera dele. Nada o verifica depois — a 2026-09-08 um
  relatório registou `0` para dois scripts que saem `1`, e passou por todas as
  verificações. Um exit code errado aqui é um resultado inventado, e o funil de
  `contrato-e-evidencia.md` proíbe-o pelo nome.)
Ferramentas indisponíveis: <ferramenta — erro exacto>
Artefactos: /tmp/auditoria-<data>/
Este relatório: docs/auditorias/<data>-<âmbito>.md

## 4. Verificação
Gates críticos: X/Y resolvidos
Obrigações totais: X/Y resolvidas
PROVEN: n · CLEARED: n · UNPROVEN: n · NOT_APPLICABLE: n
(Contados **na** tabela das obrigações, nunca estimados. "Contagem aproximada"
não é uma opção que exista: se o resumo e a tabela discordarem, o errado é o
resumo — e um resumo errado no `PROVEN` é um verdict errado, porque `PROVEN` é
o estado que conta defeitos.)

## 5. Conclusão de cobertura
O que este relatório prova, em duas ou três frases.
O que continua desconhecido, e porquê.
```

Se houver evidência directa de perda de dados, execução arbitrária, update
comprometido ou exposição de credenciais — mesmo fora de âmbito — vai **antes**
do bloco 1, com o título `RISCO CRÍTICO`.

## Tabela de obrigações (obrigatória)

Antes dos findings. Contagens sozinhas não permitem verificar nada: esta tabela
é o que torna a auditoria auditável.

```markdown
## Resultado das obrigações

| ID | Estado | Gate | Evidência | Cobertura | Artefacto | Nota |
|---|---|---|---|---|---|---|
| UX-01 | CLEARED | sim | EXECUCAO | COMPLETA | capturas/ux-01-* | os 12 fluxos do mapa, todos percorridos |
| UX-02 | PROVEN | sim | EXECUCAO | COMPLETA | capturas/ux-02-cancel | ver UX-F01 |
| UX-06 | UNPROVEN | não | — | — | — | tokens não legíveis sem build |
| RUST-02 | UNPROVEN | sim | ANALISE_ESTATICA | AMOSTRA | — | `catch_unwind` do worker testado; as ~190 ocorrências de `unwrap`/`expect` em `tools`/`editor` não foram abertas |
| A11Y-08 | NOT_APPLICABLE | não | LEITURA | COMPLETA | — | app não faz zoom próprio nem tem animações — confirmadas as duas ausências |
```

Todas as obrigações activadas aparecem. Gates críticos primeiro. **Nenhuma
linha fica `PENDING`**: se não se verificou, é `UNPROVEN` com a razão na coluna
Nota. `OUT_OF_SCOPE` não é estado de obrigação — pertence a detecções e áreas.

**Um estado por linha, sem modificadores** (`SKILL.md`), e a coluna Cobertura
diz para quanto do universo é que a evidência olhou
(`contrato-e-evidencia.md`). É o par Estado × Cobertura que se lê: a linha do
`RUST-02` acima é a diferença entre "isto está bem" e "isto está bem na parte
que abri" — a segunda não fecha um gate que pede universalidade.

## Findings

Um por causa-raiz. Nunca um por sintoma.

```markdown
### <ID> — <título: o defeito, não a sugestão>

- **Estado**: CONFIRMED
- **Prioridade**: P0 | P1 | P2 | P3
- **Confiança**: ALTA | MEDIA | BAIXA (só admissível em P2/P3 — ver abaixo)
- **Área**: <módulo>
- **Plataforma**: todas | Windows | macOS | Linux
- **Localização**: `caminho:linha`
- **Fluxo**: <qual dos fluxos mapeados>
- **Trigger**: <a sequência concreta que provoca isto>
- **Caminho de execução**: <UI → hook → invoke → comando → ...>
- **Causa-raiz**: <a coisa que está errada, não o sintoma>
- **Consequência**: <o que acontece ao utilizador ou ao comprador>
- **Evidência**: <tipo> — <o que se observou>
- **Teste existente**: <o que existe hoje, ou SEM_PROVA>
- **Decisão relacionada**: <entrada em DECISOES.md / riscos-aceites.md>
- **Correcção mínima**: <a mudança mais pequena que resolve>
- **Verificação necessária**: <como se prova que ficou resolvido>
- **Esforço**: <ordem de grandeza>
- **Dependências**: <findings que têm de vir primeiro>
```

IDs estáveis: prefixo do módulo e número (`SEC-F01`, `UX-F03`). Um finding que
já existia numa auditoria anterior reutiliza o ID e é assinalado como
reincidência.

**Os números vêm dos baselines, e não do relatório.** `achados-resolvidos.md`,
`riscos-aceites.md` e `ultima-auditoria.md` são a única memória de que números
estão tomados — é por isso que a fase 0 os lê e a fase 4 propõe escrevê-los. Um
número que já lá esteja tem dono: ou é o mesmo defeito outra vez, e diz-se
reincidência, ou é outro, e leva o número livre seguinte. Reutilizá-lo em
silêncio parte a chave do `achados-resolvidos.md` — a 2026-09-08 cinco IDs
nomeavam dois defeitos diferentes no mesmo dia, e o `DIST-F02` de um relatório
era o `DIST-F01` de outro. O `validate_report.py` recusa esse caso.

Enquanto os baselines não forem escritos, esta memória não existe: uma
auditoria que os proponha e não os veja colados recomeça em `F01` na vez
seguinte.

**Título**: descreve o defeito. "Cancelar exportação deixa o processo FFmpeg a
correr" — não "melhorar o cancelamento".

## Prioridades

| P | Critério |
|---|---|
| `P0` | Exploração, perda de dados generalizada, ou distribuição comprometida |
| `P1` | Impede vender: falha grave num fluxo principal, indisponibilidade persistente, ou impedimento legal |
| `P2` | Defeito material, ou dívida que já causa custo recorrente |
| `P3` | Melhoria localizada, polish |

P0 ou P1 aberto dá `FAIL`. Não existe P1 compatível com `PASS` ou `CONCERNS`:
se a consequência não impede vender, é P2. Um P1 formalmente aceite deixa de
ser finding activo e passa a `ACCEPTED_RISK`, com entrada em
`baselines/riscos-aceites.md` — mitigação conhecida mas não aplicada não conta.
**`P0` nunca passa a `ACCEPTED_RISK`**: corrige-se, não se aceita para dar
`PASS`.

Não inflacionar P0/P1: se tudo é crítico, nada é. Mais do que uns poucos P3 é
sinal de que a auditoria fugiu para revisão de estilo; agrupar por causa comum.

**Não listar o que está bem**, excepto para delimitar o risco ("a validação de
caminhos está correcta na exportação; o problema é só na importação").

## Alertas por confirmar

Uma suspeita grave sem prova suficiente **não** é um finding `CONFIRMED` P0/P1.
Vai numa secção própria, logo a seguir à abertura:

```markdown
## ALERTA PRECAUCIONÁRIO — por confirmar
<o que se observou> · <porque poderia ser grave> · <o que falta para confirmar>
```

Isto preserva a urgência sem quebrar o funil de evidência. Confiança `BAIXA`
**nunca sustenta um finding P0/P1**: esse caso vai sempre para aqui, e não para
a lista de findings. Em `P2`/`P3`, `BAIXA` é admissível directamente no
finding (ver `contrato-e-evidencia.md`) — a diferença é a prioridade em jogo,
não a secção.

## Hipóteses

Depois dos findings, sem prioridade. Candidatos que não passaram o funil mas
valem investigação, cada um com **a medição ou o teste que os confirmaria**.

## Fecho

```markdown
## Bloqueadores para vender
<os P0/P1 que impedem cobrar dinheiro por isto>

## Por onde começar
<ordem por dependências e redução de risco, não por prioridade pura. Um P2 que
desbloqueia três P1 vem primeiro.>

## Fora de âmbito
<OUT_OF_SCOPE detectados — uma linha cada, com o módulo recomendado>

## Não verificado
<UNPROVEN, com a razão concreta e o que seria preciso>
<NOT_APPLICABLE, com a justificação>

## Checklist: X/Y  (gates críticos: X/Y)

## Riscos residuais
<o que continua desconhecido depois desta auditoria>

## Para registar nos baselines
<bloco pronto a colar em ultima-auditoria.md, e entradas novas para
achados-resolvidos.md e riscos-aceites.md — proposto, não escrito>
```

## Erros a não cometer

- Escrever "parece que" sem dizer se é facto, inferência ou hipótese.
- Dar prioridade a um item cuja consequência não foi descrita.
- Repetir a mesma causa em três findings porque tem três sintomas.
- Recomendar uma ferramenta sem apontar o defeito que ela resolve aqui.
- Terminar sem a tabela de obrigações, sem `Checklist` ou sem os `UNPROVEN`.
- Resumir contagens "por alto" em vez de as contar na tabela.
- Inventar estados compostos (`CLEARED (decisão)`, `PROVEN (matiz)`) em vez de
  escolher um e pôr o resto na Nota.
- Fechar uma obrigação de universalidade com evidência de cobertura `AMOSTRA`.
- Dar `CLEARED` a uma obrigação incumprida por haver uma decisão a justificá-la.
- Reportar cobertura `BLOCKED` sem a fracção e sem dizer o que a desbloqueia.
- Aplicar correcções. A auditoria acaba no relatório.
