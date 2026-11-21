# Próxima sessão: pqr-security-hunt depois da 5.4.0

Escrito a 2026-11-21, depois da caça 2 ao Forma e da comparação com três ferramentas de auditoria
de segurança (Cloudflare, Google Mantis, OpenAI Codex Security). Ler isto e depois decidir o que
fazer. O que já está feito está no `git log`; aqui fica o estado, o que falta, e o contexto que
não está no código.

## 1. Estado do plugin

Todas as instalações estão em **5.4.0**: no Forma (`C:\a\forma\GestaoProjectosArq`, plugins
`production-quality-ready` e `pqr-security-hunt`) e no JustClip (`C:\a\justclip\JustClip`, plugins
`production-quality-ready`, `pqr-desktop`, `pqr-process` e `pqr-ui-system`). Este repositório
tem só o `main`.

O que cada versão trouxe ao `pqr-security-hunt`:

| Versão | PR | O que entrou |
|---|---|---|
| 5.1.0 | #5 | A skill: o modelo de ameaças orienta o plano; o `hunt.py check` impõe o orçamento de agentes; um achado só é confirmado por um teste vermelho do próprio projecto (`prove`); `reprove`; `emit` escreve evidência FAIL para o `security-audit` |
| 5.2.0 | #6 | O `adopt` fecha um achado corrigido com o teste de regressão do projecto, e o `found_at` guarda o commit onde a trace foi lida; cinco cartões de classe novos (`iso.namespace-collision`, `auth.revocation-lifecycle`, `authz.derived-copy`, `logic.declared-size`, `cost.per-target-ceiling`); `plan.external` para auditorias de fora |
| 5.2.1 | #8 | O ratchet de SEO do `audit-website` (`web.seo-no-regression`). Não é do security-hunt |
| 5.3.0 | #9 | O **crítico de cobertura** (papel `critic`, `raised_by` nas unidades); o verificador monta o estado do ataque directamente, para a prova sobreviver à correcção; o passo 7 «corrigir» (o alcance todo primeiro, dois testes) |
| 5.4.0 | #11 | O `adopt` só fecha um achado se o teste **falhar no código por corrigir**: corre numa worktree no `found_at` e o resultado `held` é recusado, `red` fica como baseline, `unproven` fica dito. Também `rebaseline`, `record` (escreve no ledger as respostas dos agentes), `stale` (unidades cujo código ou cartão mudou) e os avisos de duplicados no `check` |

O `hunt.py` está dividido em `hunt.py` (CLI, `check`, `prove`, `reprove`, `adopt`, `emit`),
`hunt_core.py`, `hunt_baseline.py` e `hunt_record.py`.

## 2. O que falta, por ordem

1. **Re-atacar cada correcção (ideia 2 da comparação, Mantis).** Um agente novo recebe a
   afirmação, o cartão e o diff da correcção, e tenta pelo menos 3 variantes: outra rota, outro
   papel, outra codificação. Mudanças a fazer:
   - um brief «re-atacante» em `agents.md`, com o papel de verificador;
   - um campo `variants[]` nos achados, corrido por `hunt.py prove <fp> --variants`;
   - o `adopt` regista `variants: held×N`, ou `narrow` com menos de 3, e qualquer `red` mantém o
     achado `confirmed`.

   Custo: 1 agente por correcção e cerca de 60 linhas. É a resposta ao que aconteceu com o
   «kick» da revogação, que corrigimos num caminho quando faltava em mais cinco.
2. **`adopt --baseline-from-proof`.** Quando o teste de regressão importa código que só a
   correcção cria, a baseline fica `unproven` (foram 3 casos na caça 2: `uploadLimit`, o serviço
   de multipart e o `csvCell` partilhado). Nesses casos a prova do verificador falhou no mesmo
   `found_at` e o log ainda existe. A ideia é usar esse log como baseline e marcá-lo como tal,
   em vez de `unproven`.
3. **Sementes do histórico do git (ideia 6, Mantis `mantis-history`).** `hunt.py seeds` lista as
   correcções de segurança antigas e os ficheiros de produção que tocaram. Servem só para o
   passo 3 (planear fronteiras e unidades «irmãs»), nunca entram num brief de caçador, para não
   ancorar a caça. Custo: cerca de 40 linhas, sem agentes.
4. **O `threat_model.py` do `security-audit` não vê linhas desactualizadas.** Só confirma que o
   ficheiro citado existe. No Forma deu PASS com 6 de 13 referências a apontar para um
   comentário, uma linha em branco ou um `}` (corrigido no PR #47 do Forma). Proposta: recusar
   uma citação cuja linha esteja em branco ou seja só pontuação ou comentário, ou guardar um
   excerpto como as traces do hunt.
5. **Briefs de agentes que corrigem código numa worktree.** O `biome.json` do Forma exclui
   `**/.claude`, por isso o `pnpm lint` numa worktree em `.claude/worktrees/` não analisa nada
   (os 4 agentes da caça 2 bateram nisto). O passo 7 do `SKILL.md` deve dizer que o lint final
   se corre na checkout principal depois de juntar os ramos.
6. **Item 6, caçadores largos contra estreitos: medir outra vez.** A caça 2 caçou as mesmas 4
   unidades (U15–U18) com 1 caçador largo e com 4 estreitos:
   - o largo gastou 192 k tokens e trouxe 3 candidatos;
   - os estreitos gastaram 486 k tokens (2,5×) e trouxeram 5;
   - só os estreitos viram a quota contornada no multipart (depois confirmada) e as fórmulas no
     CSV;
   - só o largo viu dois caminhos paralelos dos mesmos defeitos.

   Uma amostra de 4 unidades não chega para mudar o orçamento por omissão. Proposta: estreito
   só nas classes com vários sumidouros distintos (`input.upload`, `input.markup-injection`),
   largo no resto, e comparar outra vez.
7. **Mais tarde:**
   - lições entre caças para os verificadores (Mantis `reflect`), só quando houver provas
     `broken` suficientes para aprender alguma coisa (até agora houve uma);
   - encadear achados confirmados (Mantis `chain`), que vale pouco com 4 confirmados.

## 3. O Forma, do lado da caça

O ledger está em `C:\a\forma\GestaoProjectosArq\.audit\security-hunt\` (`plan.json`, `findings.json`,
`proofs/`, e `run2/` com as respostas e os custos de cada agente da caça 2). Esta pasta não está
no git.

- **Caça 1** (2026-11-19): 6 agentes, 10 achados, todos corrigidos.
- **Comparação com a Cloudflare** (2026-11-20): 7 achados que nos escaparam, todos corrigidos e
  registados como fonte externa `cf-audit` (U19–U25).
- **Caça 2** (2026-11-20): 20 agentes (12 caçadores, 1 crítico, 7 verificadores). As 7 zonas do
  crítico da Cloudflare e as 4 que tinham ficado fora (U15–U18).
  - Confirmados: 4 (1 HIGH, 3 MEDIUM). Mais 1 `needs_validation` e 4 candidatos.
  - Tudo corrigido no PR #48 do Forma, em produção na versão 1.144 com as migrações 0103 e 0104.
  - Pelo caminho encontrou e corrigiu três bugs de produção: os aditamentos falhavam desde
    1/ago; os backups automáticos acabavam `failed` e a retenção nunca corria; os clientes
    convidados pela página da equipa entravam com o papel `member`.
- **Estado do ledger:** 26 achados `fixed`, `check` sem erros. Baselines: 6 `red` e 3
  `unproven` nos achados da caça 2.
  - Os 17 achados antigos foram passados pelo `rebaseline`: 14 deram `red` e 3 `unproven`
    (o teste importa código que só a correcção criou). Nenhum deu `held`, ou seja, nenhum fecho
    antigo estava assente num teste que não prova nada.
  - No total: 20 `red`, 6 `unproven`, 0 `held`. O item 2 da secção 2 (`--baseline-from-proof`) trataria os 6 `unproven`.
- **Próxima caça.** As 12 zonas que o crítico levantou e nenhuma caça leu estão `deferred`
  (U33–U44):
  - o serviço de equipa (hierarquia e revogação na desactivação);
  - o dono temporário e a suspensão do atelier pelo super;
  - os 4 routers `/api/super`;
  - o signup anónimo (custo e enumeração);
  - as passwords Argon2id e o MFA TOTP;
  - os uploads de logótipo e avatar;
  - o SMTP do atelier (ligação de saída);
  - o mapeamento FK→404;
  - o `/api/health/ready`.
- **Primeira utilização do 5.4 numa caça:** usar `hunt.py record` em vez de copiar respostas à
  mão, e `hunt.py stale` no passo 3.

## 4. As ferramentas comparadas

### Cloudflare — `cloudflare/security-audit-skill`

- **O que é:** uma skill de auditoria de segurança com agentes, que exige uma sandbox do sistema
  operativo para confirmar achados.
- **Como a corremos:** a 2026-11-20, sobre o commit `6e3a0787` do Forma (antes das correcções
  da caça 1), no mesmo âmbito e sem pistas. Usou 16 agentes e cerca de 2,1 M tokens. Os
  artefactos estão em `~/security-audit-skill/forma/run-1/` (`REPORT.md`, `findings.json`,
  `coverage-ledger.json`).
- **Resultado:** encontrou 6 defeitos reais que a caça 1 não viu, mas não confirmou nenhum,
  porque no Windows não há a sandbox que exige. Apanhou 5 das nossas 10 conclusões por inteiro e
  3 em parte; falhou as duas de custo de leitura da D1. O crítico dela apontou as 7 zonas que a
  caça 2 caçou.
- **Os 6 que nos escaparam, e a classe que os teria apanhado:**

  | Achado | Classe (cartão novo na 5.2.0) |
  |---|---|
  | `/quotes/project:<P>/chat` entrava na sala do projecto P | `iso.namespace-collision` |
  | A mudança de email pendente sobrevivia à mudança de password | `auth.revocation-lifecycle` |
  | O acesso do cliente sobrevivia à reatribuição ou desactivação | `auth.revocation-lifecycle` |
  | Os totais de honorários em cache saíam a quem não tem finanças | `authz.derived-copy` |
  | Um restauro com `size_bytes` inventado punha a quota a zero | `logic.declared-size` |
  | O reset de password tinha tecto por IP mas não por conta | `cost.per-target-ceiling` |

- **O que adoptámos:** os 5 cartões, o `plan.external` e o crítico de cobertura (5.3.0).
- **O que não copiar:**
  - a sandbox obrigatória, que no Windows impede qualquer confirmação;
  - os validadores que recusam correr no Windows (`O_NOFOLLOW`), que tiveram de correr no WSL;
  - os prompts de cerca de 40 KB por agente;
  - 16 agentes para 11 candidatos, com 6 por verificar.

  O ganho da Cloudflare está no **que** procura, não no processo.

### Google Mantis — `google/mantis` (Apache-2.0)

- **O que é:** publicada em Junho de 2026, em Python. São 19 skills `mantis-*` para agentes de
  código (Gemini CLI, Antigravity e outros, pelo formato de skills) e um harness de referência
  sobre o Google ADK. Instala-se com `npx skills add google/mantis`. Diz não ser um produto
  oficialmente suportado pela Google.
- **Fluxo:**
  - modelo de ameaças, índice estrutural, histórico do git (`mantis-history`), investigação,
    deduplicação, crítico;
  - reprodução (`mantis-reproduce`, em gVisor ou numa VM sem rede);
  - encadeamento (`mantis-chain`), patch e re-ataque (`mantis-patch`);
  - calibração do risco de 1 a 10 (`mantis-calibrate`), lições guardadas (`mantis-reflect`),
    relatório;
  - um supervisor, `mantis-meta-agent`, corre o ciclo inteiro.
- **Ideias-chave:**
  - não há `VERIFIED_SECURE` sem o reprodutor disparar primeiro numa cópia por corrigir
    (`mantis-patch.md`, bloco G, passo 1);
  - o re-ataque exige pelo menos 3 variantes, e menos do que isso dá `INCOMPLETE`;
  - os scripts actualizam o JSON em vez de o modelo o reescrever («Token-Optimized File
    Updates»);
  - a deduplicação tem três níveis: o nível 1 compara ficheiro, classe e símbolo, ou linhas a
    menos de 3 de distância, e só marca `possible_duplicate_of`.
- **A alegação de «85 % menos tokens»:** não está no repositório. As técnicas que lá estão são:
  - prompts de cada fase injectados directamente;
  - contexto isolado por fase;
  - limpeza da saída de ferramentas antiga quando o pedido chega a 85 % do limite (provável
    origem do número, em `reference/core/graph_loader.py`);
  - scripts auxiliares em vez de reescrever JSON.
- **O que adoptámos na 5.4.0:**
  - a baseline no código por corrigir (`adopt`);
  - o `record`;
  - o `stale` (inspirado no `--scan-mode changed` e na impressão digital da cobertura);
  - o aviso de duplicados, que corresponde ao nível 1 da deduplicação.
- **Por adoptar:** o re-ataque com variantes, as sementes do histórico, as lições e o
  encadeamento (secção 2).
- **O que não copiar:**
  - a pontuação de risco numérica (27 regras de tecto), porque a nossa severidade é a que o
    teste vermelho demonstra;
  - a sandbox gVisor/VM, que não corre no Windows nativo;
  - a GitHub Action de PR, que a própria Mantis diz não estar testada;
  - as skills de 10 a 47 KB cada (223 KB nos 8 ficheiros lidos);
  - o snapshot pinning, porque o nosso `found_at` mais o `git show` fazem o mesmo.
- **Fontes lidas:** os ficheiros `critic`, `patch`, `calibrate`, `reflect`, `dedupe`, `history`,
  `reproduce` e `chain` foram descarregados para
  `C:\Users\joaoc\AppData\Local\Temp\tmp.dhaTzFxcVh\`, uma pasta temporária que pode desaparecer.
  Para os voltar a buscar: `gh api repos/google/mantis/contents/skills/<nome>/SKILL.md -H
  "Accept: application/vnd.github.raw"`.

### OpenAI Codex Security — `openai/codex-security` (Apache-2.0)

- **O que é:** o agente de segurança da OpenAI, com quatro formas: um plugin no Codex, um CLI e
  SDK TypeScript abertos (npm `@openai/codex-security`, comando `cs`), revisão de PRs no GitHub,
  e o Codex Security Cloud. Há também uma GitHub Action oficial (`openai/codex-security@<commit>`)
  com saída SARIF, contagens por severidade e um tecto de custo; o exemplo dela usa cerca de 5 $
  por scan.
- **Comandos:**
  - `cs scan .` e `cs scan . --diff origin/main` (só o que mudou);
  - `--mode deep`, que repete scans e junta os resultados;
  - `--patch`, que gera correcções;
  - `--max-time 15`, um tecto de tempo indicativo;
  - `cs export --artifact threat-model`;
  - exportação em SARIF, JSON e CSV;
  - importação de alertas de outros scanners;
  - publicação para o Linear, o Jira ou o GitHub.
- **Configuração:** o `SECURITY.md` do repositório e de cada componente. Fornecedores de modelo:
  OpenAI, OpenRouter, Fireworks e Amazon Bedrock.
- **Ideias-chave:**
  - a skill `verify-fix` não aceita «testes não relacionados a passar» como prova de correcção;
  - a correcção é revista por um revisor novo, que recebe o diff mas não o raciocínio de quem
    corrigiu;
  - a política de severidade suprime o impacto que só afecta o próprio chamador.
- **O que adoptámos:** a exigência de prova na correcção, que entrou como baseline do `adopt`.
  O revisor novo é a base da ideia 2 (re-ataque), ainda por fazer.
- **O que não copiar:**
  - a Action e o SARIF, que precisam de chave da OpenAI e de runner hospedado, e a nossa saída
    alimenta a evidência do `security-audit` e não o code scanning;
  - o scan profundo «repete até não acrescentar nada», que não tem tecto de custo (o nosso é
    aprovado pela pessoa);
  - os 20 importadores de scanners, porque o `plan.external` já recebe fontes de fora;
  - a deduplicação por dois modelos, pesada para 26 achados.
- **Verificar nos cartões de authz/logic:** que dizem que «só os dados do próprio chamador» vale
  no máximo LOW. A Codex suprime esse impacto e a Mantis põe-lhe o tecto em LOW.

**Fontes:**
- [openai/codex-security (README)](https://github.com/openai/codex-security/blob/main/README.md)
- [Codex Security — GitHub Action](https://github.com/openai/codex-security/blob/main/github-action/README.md)
- [byteiota — Codex Security: validate, patch, verify](https://byteiota.com/openai-codex-security-cli/)
- [google/mantis](https://github.com/google/mantis)
- [MarkTechPost — Google open-sources Mantis](https://www.marktechpost.com/2026/09/09/google-open-sources-mantis-a-modular-skills-toolkit-that-lets-coding-agents-find-reproduce-and-patch-vulnerabilities/)
- [aicybr — Google Mantis: arquitectura e sandbox](https://aicybr.com/blog/google-mantis-ai-vulnerability-scanning-harness-guide)
