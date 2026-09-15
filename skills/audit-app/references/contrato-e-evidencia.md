# Contrato e evidência

**Aviso — hierarquia.** Este ficheiro é a **tradução operacional** do
`CONTRACTS.md` da raiz do plugin para quem opera uma auditoria. Não é
autoritativo. Onde este ficheiro e o `CONTRACTS.md` contradisserem-se, o
`CONTRACTS.md` ganha e este ficheiro é defeito.

**Traduções principais entre este ficheiro e o `CONTRACTS.md`:**

| Aqui | `CONTRACTS.md` |
|---|---|
| `CANDIDATE` / `CONFIRMED` / `DISMISSED` / `ACCEPTED_RISK` / `OUT_OF_SCOPE` | Vocabulário de detecção (informal) |
| `PROVEN` / `CLEARED` / `UNPROVEN` / `NOT_APPLICABLE` | Verdicts §3.1 `result:` — `PASS` / `FAIL` / `NOT_VERIFIED` / `NOT_APPLICABLE` |
| `COMPLETE` / `PARTIAL` / `BLOCKED (n/m)` | Cobertura §4.3 |
| Tipos de evidência (`EXECUCAO` / `TESTE` / `MEDICAO` / `LEITURA` / etc.) | §3.4 `evidence[].kind` (`source` / `screenshot` / `log` / `measurement` / `command-output` / `external`) |

Este ficheiro herda a lógica de decisão (funil, precedência, exclusões,
cobertura declarada); o formato de dados vive no `CONTRACTS.md`. Uma skill
que emite evidência escreve o schema do `CONTRACTS.md`, não este vocabulário.

Carregado em **todos** os módulos que a `audit-app` orquestrar. É a única
referência que nunca é opcional.

Índice: [Funil](#funil-do-candidato-ao-finding) ·
[Decisão documentada](#decisão-documentada-não-fecha-uma-obrigação) ·
[Tipos de evidência](#tipos-de-evidência) ·
[Cobertura do método](#cobertura-do-método) ·
[Provar uma ausência](#provar-uma-ausência)
· [Precedência](#precedência) · [Confiança](#níveis-de-confiança) ·
[Ferramentas indisponíveis](#ferramentas-indisponíveis) ·
[Falsos positivos](#evitar-falsos-positivos) · [Exclusões](#declarar-exclusões)
· [Artefactos](#artefactos-temporários) · [Fecho](#fecho-com-cobertura-verificável)

## Funil: do candidato ao finding

Tudo o que um grep, linter, scanner, subagente ou intuição produz entra como
`CANDIDATE`. Um candidato sobe a `CONFIRMED` só depois de responder às cinco
perguntas:

1. **Caminho** — que ficheiro e que linha? Lido, não presumido.
2. **Trigger** — que sequência real de utilização chega ali? Se não se
   consegue descrever a sequência, é hipótese, não finding.
3. **Consequência material** — o que acontece ao utilizador ou ao comprador?
   "Não é idiomático" não é consequência. "Perde as legendas editadas ao
   exportar com o projecto aberto há mais de uma hora" é.
4. **Alcance** — acontece sempre, em condições específicas, ou só em teoria?
   Em que plataformas?
5. **Ainda existe** — foi confirmado no código actual, e não apenas na memória
   de uma auditoria anterior.

Falha em qualquer uma → o candidato vai para `DISMISSED` (com uma linha a dizer
porquê) ou fica como hipótese explicitamente rotulada no fim do relatório, sem
prioridade atribuída.

`ACCEPTED_RISK` só se existir entrada correspondente em
`baselines/riscos-aceites.md` **e** as condições de reabertura registadas lá
não se verificarem. Se se verificarem, o risco reabre e vira `CANDIDATE`
outra vez.

## Decisão documentada não fecha uma obrigação

Uma decisão, um ADR ou uma entrada de risco provam que a condição é
**consciente** e, quando aplicável, **aceite**. Não transformam uma obrigação
tecnicamente incumprida em `CLEARED`: `CLEARED` diz que a condição problemática
não está presente, e nenhuma decisão a faz desaparecer.

| Situação | Estado da obrigação | Registo adicional |
|---|---|---|
| A condição é cumprida | `CLEARED` | — |
| Não é cumprida, e não há decisão | `PROVEN` | finding |
| Não é cumprida, mas há decisão válida | `PROVEN` | `ACCEPTED_RISK` |
| Há alternativa permitida, cumprida e comprovada | `CLEARED` | evidência da alternativa |
| Há alternativa, mas só documentada | `UNPROVEN` | decisão por cumprir |

Aplica-se a tudo o que costuma aparecer justificado em vez de verificado: CI
inexistente, `fmt`/`clippy` que ninguém corre, advisories aceites, ausência de
logs, ausência de testes automatizados, dependências sem manutenção.

O risco aceite muda a **agregação** do verdict pela prioridade residual (ver
`SKILL.md`); não muda a realidade técnica que ficou registada na linha. É essa
a diferença entre uma auditoria e uma acta.

## Tipos de evidência

Do mais forte para o mais fraco:

| Tipo | O que é | Cuidado |
|---|---|---|
| `EXECUCAO` | Comportamento observado a correr a app ou o binário | Registar comando, ambiente, versão, o que se observou |
| `TESTE` | Teste reproduzível que falha/passa por causa disto | O teste tem de falhar pela razão certa (ver `testes.md`) |
| `MEDICAO` | Número obtido com metodologia declarada | Sem baseline e workload, um número não é evidência |
| `ANALISE_ESTATICA` | Ferramenta que analisa sem correr o código: typecheck, compilador, linter, grep, scanner | Vale pelo que a ferramenta garante e pela [cobertura](#cobertura-do-método) declarada. Com `PARCIAL` ou `AMOSTRA`, **nunca sozinha sustenta um finding** |
| `LEITURA` | Leitura de código com raciocínio explicado | Válida se o raciocínio for verificável por terceiros |
| `DOCUMENTO` | `CLAUDE.md`, `DECISOES.md`, comentário no código | Prova intenção, não comportamento |
| `FONTE_EXTERNA` | Documentação oficial da versão instalada | Ver [regras](#fontes-externas) |

## Cobertura do método

O tipo de evidência diz **como** se olhou. Não diz **para quanto**. Cada linha
declara as duas coisas, e é a segunda que decide o que a primeira pode fechar:

| Cobertura | Significado |
|---|---|
| `COMPLETA` | Completa dentro do universo **declarado na nota** — não "li os ficheiros que me pareceram" |
| `PARCIAL` | Parte do universo ficou por examinar, e sabe-se qual |
| `AMOSTRA` | Alguns casos, escolhidos por conveniência ou por representatividade |

As regras que dão dentes à coluna:

- `AMOSTRA` **nunca fecha** uma obrigação que exige universalidade ("nenhum
  `unwrap` fora de testes", "nenhuma chave em falta"). O melhor que produz é
  `UNPROVEN`, com o que se viu registado na nota.
- `PARCIAL` não produz `CLEARED` se a parte não examinada puder mudar a
  conclusão.
- `COMPLETA` obriga a nota a dizer **que universo** e **que exclusões**. Sem
  isso é `PARCIAL` com outro nome.

Uma observação positiva sobre um mecanismo continua válida com `AMOSTRA` — o
que ela não faz é fechar a obrigação sobre as ocorrências que ninguém abriu.

Os scripts desta skill já emitem este juízo por si: o `i18n_keys.py` fecha com
`cobertura completa: NAO → a parte não coberta fica UNPROVEN`, e o
`ipc_inventory.py` com `isto NÃO é 'zero problemas' — é 'não sei'`. Transcrever
essa declaração para a linha é o mínimo; ignorá-la é inventar cobertura que a
própria ferramenta recusou dar.

## Provar uma ausência

"Não existe X" é a afirmação mais fácil de escrever e a mais difícil de
sustentar: um grep que não encontra nada devolve o mesmo silêncio quer X não
exista, quer se tenha procurado no sítio errado ou com o nome errado. Uma
ausência é sempre uma afirmação de universalidade, e por isso **exige cobertura
`COMPLETA`** — com `AMOSTRA` ou `PARCIAL` o resultado é `UNPROVEN`, não
`CLEARED`.

Quem afirma uma ausência declara, na nota, as quatro coisas:

1. **Universo** — que ficheiros e que extensões foram percorridos, a partir de
   que raiz.
2. **Exclusões** — o que ficou de fora (`target/`, `node_modules/`, gerados) e
   porquê.
3. **Termos** — o que se procurou. Uma dependência procura-se no manifesto
   **e** no lockfile; uma funcionalidade procura-se pelos nomes que ela teria,
   não por um só.
4. **O que escaparia** — nomes construídos por concatenação, macros,
   reexports, chamadas dinâmicas, código noutra linguagem.

Sem as quatro, a ausência é uma hipótese com ar de facto. Com elas, é uma
conclusão com âmbito — que é tudo o que este contrato pede a qualquer outra.

## Precedência

Quando duas evidências discordam:

`EXECUCAO` > `TESTE` > `MEDICAO` > `ANALISE_ESTATICA` > `LEITURA` >
`DOCUMENTO` > `FONTE_EXTERNA`

Entre evidências do mesmo tipo, ganha a de cobertura maior. E quando a
diferença de tipo é de um degrau só, é a cobertura que desempata: uma
`ANALISE_ESTATICA` de cobertura `AMOSTRA` não ganha a uma `LEITURA` que
percorreu o caminho todo.

O caso mais comum é o documento dizer uma coisa e o código fazer outra. O
código ganha, e a divergência é ela própria um candidato — documentação errada
sobre segurança ou sobre o formato do projecto tem consequência material.

## Níveis de confiança

Cada finding declara um:

- `ALTA` — reproduzido, ou provado por duas evidências independentes de tipo
  forte. Aguenta contestação.
- `MEDIA` — código lido e caminho identificado, sem reprodução. A causa é
  clara mas o alcance exacto não foi medido.
- `BAIXA` — inferência plausível a partir de leitura parcial. Admissível em
  P2/P3. **Nunca sustenta um finding `CONFIRMED` P0/P1**: uma suspeita grave
  sem prova vai para `ALERTA PRECAUCIONÁRIO` (ver `relatorio.md`), o que
  preserva a urgência sem quebrar o funil.

Não usar `ALTA` para compensar falta de tempo. A confiança declarada é a coisa
que torna o relatório utilizável por outra pessoa.

## Ferramentas indisponíveis

Quando um comando previsto não existe ou falha:

1. Registar o comando exacto e o erro exacto.
2. Marcar a obrigação `UNPROVEN` com essa razão.
3. Aplicar o fallback indicado na referência do módulo, se existir, e dizer que
   é fallback (cobertura menor).
4. **Não instalar nada.**
5. **Não transformar a ausência da ferramenta num finding da app.** Que
   `cargo-deny` não esteja instalado nesta máquina não é um defeito do JustClip.
   O que pode ser defeito é o CI nunca o correr — mas isso verifica-se no CI, e
   pertence a `distribuicao-supply-chain.md`.

## Evitar falsos positivos

- **Working directory.** Normalizar sempre. Ou se corre a partir da raiz do
  repositório com paths completos, ou se entra na pasta e se usam paths
  relativos a ela — nunca `cd src-tauri` seguido de `src-tauri/src/...`. Cada
  comando no relatório indica de onde foi corrido.
- **Contagens.** Nunca derivar um número de `tail -5` de um output. Usar a
  saída estruturada da ferramenta (`--format json`, `--reporter json`, ficheiro
  de resultados) ou contar explicitamente. Se não houver forma fiável, dizer
  "não foi possível contar de forma fiável" em vez de inventar um número.
- **Código morto vs código não referenciado por grep.** Antes de dizer que algo
  não é usado, procurar: reexports, chamadas dinâmicas, nomes construídos por
  concatenação, uso em macros, testes, e no lado oposto do IPC.
- **Supressões existentes.** Um `allow`, `eslint-disable` ou baseline de
  ferramenta pode ser deliberado. Ver `docs/DECISOES.md` e os baselines antes
  de reportar.
- **Diferenças de plataforma.** Um problema que só existe em Windows é um
  finding com plataforma declarada, não um finding geral.
- **Ruído gerado.** Ignorar ficheiros gerados, `target/`, `dist/`,
  `node_modules/` e bindings automáticos, salvo quando o próprio processo de
  geração é o assunto.

## Fontes externas

Quando for preciso consultar documentação:

- Preferir a fonte oficial do projecto (Tauri, React, Rust, a crate concreta).
- **Confirmar a versão.** A resposta tem de corresponder à versão instalada
  neste repositório, lida do lockfile — não à última versão publicada, nem à
  que se recorda. Ecossistemas como Tauri 2 e React lançam com frequência; o
  que era verdade há um ano frequentemente já não é.
- Citar a fonte e a data de consulta.
- Distinguir "isto é o comportamento actual da versão X" de "isto era assim
  quando aprendi". Se não for possível confirmar na versão instalada, é
  hipótese, e diz-se.
- Uma recomendação externa não é finding. Vira finding quando se demonstra o
  defeito concreto que ela resolve neste repositório.

## Declarar exclusões

O relatório declara explicitamente, com uma frase por item:

- módulos não pedidos;
- obrigações `NOT_APPLICABLE` e porquê;
- plataformas não testadas (habitualmente as que não se conseguiu executar);
- áreas onde a capacidade de execução era `STATIC` ou `ASSISTED`;
- ficheiros ou zonas deliberadamente não lidos, e a razão.

Uma exclusão declarada é honesta. Uma exclusão silenciosa é o que faz um
comprador descobrir o problema em vez do vendedor.

## Artefactos temporários, e o relatório

**A matéria-prima** fica fora do repositório, em `/tmp/auditoria-<AAAA-MM-DD>/`
— é volumosa, é descartável, e não é ela que se lê daqui a seis meses:

```
/tmp/auditoria-2026-09-06/
├── comandos.log        # comando, cwd, exit code, duração
├── outputs/            # stdout/stderr integrais das ferramentas
├── capturas/           # screenshots, com nome = estado capturado
└── medicoes/           # dados brutos das medições de performance
```

**O relatório não.** Vai para `docs/auditorias/AAAA-MM-DD-<âmbito>.md`, dentro
do repositório, versionado com o código que descreve — e o relatório indica
onde ficaram os artefactos que o sustentam. As regras de escrita (ordem em
relação à comparação Git, e nunca por cima de um relatório anterior) estão no
`SKILL.md`, em Modo read-only.

A razão de o relatório ter morada fixa e os artefactos não: um relatório é
indexável e um `/tmp` é apagado. Um índice que aponte para um relatório que já
não existe não é um índice — é uma nota a dizer que houve uma auditoria.

## Fecho com cobertura verificável

Não é permitido terminar com "auditei o que dava". Terminar com:

1. A tabela de obrigações de `relatorio.md`, com uma linha por obrigação
   activada, e `Checklist: X/Y` com contagem separada para os gates críticos.
   Os dois eixos do verdict (produto e cobertura) reportam-se sempre juntos.
2. Lista das `UNPROVEN` com a razão de cada uma.
3. Lista das `NOT_APPLICABLE` com a justificação.
4. Lista dos `OUT_OF_SCOPE` detectados e o módulo recomendado.
5. Riscos residuais: o que continua desconhecido depois desta auditoria.

Se as três primeiras listas estiverem vazias numa auditoria `full`, isso é
suspeito e deve ser reexaminado — auditorias honestas de sistemas reais quase
sempre deixam alguma coisa por provar.
