# Próxima sessão: plugin 5.3.0 (pqr-security-hunt) — a 5.2.0 saiu a 2026-11-20 (PR #6) — o que aprendemos com a Cloudflare

Escrito a 2026-11-20. Ler isto e depois decidir o que fazer.

## Contexto em 5 linhas

- O plugin 5.1.0 (main `fb3cfa4`) tem o `pqr-security-hunt`: o modelo de ameaças orienta o reconhecimento, o `hunt.py check` impõe o orçamento de agentes,
  um achado só é confirmado por um teste vermelho (`hunt.py prove`), o `reprove` corre sem agentes e o `emit` escreve evidência FAIL.
- A 2026-11-19 a caça no Forma (6 agentes) deu 10 conclusões, todas corrigidas.
- A 2026-11-20 corri a `cloudflare/security-audit-skill` no mesmo âmbito, sobre o commit de antes das correcções (`6e3a0787`), sem lhe dar pistas.
  Usou 16 agentes e cerca de 2,1 M tokens. Artefactos em `~/security-audit-skill/forma/run-1/` (`REPORT.md`, `findings.json`, `coverage-ledger.json`).
- **A Cloudflare encontrou 6 defeitos reais que a nossa caça não viu**, mas não confirmou nenhum, porque no Windows não há a sandbox que ela exige.
  Apanhou 5 das nossas 10 conclusões por inteiro e 3 em parte. Falhou as duas de custo de leitura da D1.
- Os 6 já estão corrigidos no Forma (commit `9612aab7`, cada um com o seu teste).

## Os 6 que nos escaparam, e a classe que os teria apanhado

| Achado | Classe que falta nos nossos cartões |
|---|---|
| `/quotes/project:<P>/chat` entrava na sala do projecto P (o namespace do DO é partilhado) | **colisão de namespace**: um nome de sala, chave ou caminho montado a partir de um id não validado |
| A mudança de email pendente sobrevivia à mudança de password | **revogação / ciclo de vida**: credenciais por usar depois de mudar password, email, permissões ou cliente |
| O acesso do cliente a um orçamento sobrevivia à reatribuição, desactivação ou desligar do cliente | idem (o gate confiava na linha de acesso e não no estado actual) |
| Os totais dos honorários em cache na linha do projecto saíam a membros sem finanças | **cópias derivadas**: caches, snapshots, exports e totais fora do gate |
| Um restauro com `size_bytes` inventado punha a quota a zero | **crédito a partir de um tamanho declarado** pelo cliente |
| O reset de password tinha tecto por IP mas não por conta | **tecto por alvo** (não só por origem) |

Mais: a revogação no tempo real faltava em 5 caminhos. Corrigimos o alcance do kick, mas não os caminhos que nunca chamavam kick.

## Melhorias a fazer (proposta para a 5.2.0)

1. ✅ **FEITO (commit `2259314`, publicado na 5.2.0) — `hunt.py adopt <fingerprint> <teste> --command --found-at`.** Trouxe também `found_at`: a trace de um `fixed` verifica-se no commit onde foi encontrada (antes, todo o `fixed` falhava o `check` porque a correcção mexe nas linhas citadas). Corre um teste de regressão permanente do projecto e, se passar, marca o achado como `fixed` com esse teste como prova.
   Resolve dois problemas:
   - depois de uma correcção, o `reprove` deu `broken`, porque a prova montava o ataque pelo caminho que a correcção fechou. O `check` exige `red` e o `emit` recusa o ledger inteiro;
   - as candidatas corrigidas ficavam `candidate` para sempre.
2. **Brief do verificador.** Montar o estado do atacante directamente (seed na D1) e não pelo caminho vulnerável, para a prova continuar válida depois da correcção.
3. **Passo «corrigir» no SKILL.md.** Teste vermelho e também o teste do utilizador legítimo. Em 2 casos o defeito real era maior do que o achado: o kick falhava a quem não tinha o sino aberto, e o restore descartava backups legítimos.
4. ✅ **FEITO (commit `f92a4bf`, publicado na 5.2.0) — cartões de classe novos:** `iso.namespace-collision`, `auth.revocation-lifecycle`, `authz.derived-copy`, `logic.declared-size`, `cost.per-target-ceiling`. Cada um usa um check que já existia, por isso o `CHECK_RULE` ficou igual.
   No mesmo commit, **`plan.external`**: uma auditoria de fora (id + relatório) pode ser `found_by` e `agent` de unidade, não conta para o orçamento e nunca verifica. Sem isto, os achados da Cloudflare não cabiam no ledger. Suite: 307 testes.
5. **Um crítico de cobertura barato**, 1 agente no fim da caça.
   - Recebe o plano e as unidades, e devolve as zonas que ficaram por ver como unidades `deferred` no `plan.json`.
   - O crítico da Cloudflare apontou 7 zonas que ninguém viu: o import de backups pelo super, os papéis dentro do atelier, as rotas de orçamentos e templates, o suporte com o RGPD, o custo do tempo real, o webhook do Stripe e o OAuth do Google.
6. **Opcional: hunters mais estreitos.** O ganho da Cloudflare veio de 1 unidade estreita por agente, com o bloco de classe colado no prompt. Medir antes de mudar o orçamento por omissão.

## O que NÃO copiar da Cloudflare

- A sandbox obrigatória do sistema operativo: no Windows impede qualquer confirmação.
- Os validadores que recusam correr no Windows (`O_NOFOLLOW`); tive de os correr no WSL.
- Os prompts de cerca de 40 KB por agente, e 16 agentes para 11 candidatos, com 6 que ficaram por verificar.
- O nosso modelo (o teste vermelho é a prova, o orçamento é imposto pelo script) é melhor. O ganho deles está no **que** procuram, não no processo.

## Pendentes

- **Forma:**
  - ✅ `9612aab7` em produção (v1.143, deploy do CI verde a 2026-11-20).
  - Na próxima caça, ver as 7 zonas do crítico mais as que já estavam fora: HTML nos emails/PDF, uploads, fluxos repetíveis e a confiança web→API.
  - Confirmar em produção (sem tráfego de ataque): registo self-serve, Turnstile e WAF por /64.
- ✅ **Limpeza** feita (worktree, `cf-audit-src`, `pqr-scratch`, `skills/` da raiz).
- **Ledger da caça no Forma** (`.audit/security-hunt/`):
  - ✅ os 10 estão `fixed` por `adopt` (found_at `6e3a0787`), `check` OK, `reprove` 10× held, `emit` limpou os 2 FAIL velhos;
  - ✅ os 7 da Cloudflare (os 6 da tabela + os caminhos de revogação no tempo real) entraram como fonte externa `cf-audit` (U19–U25), fechados por `adopt` com os testes de `9612aab7`: `check` OK com o plugin instalado, 17 `fixed`, `reprove` 17× held.
  - Os candidatos de finanças da Cloudflare sobre o calendário e o download do backup já eram 2 dos 10 da nossa caça.
- **Repositório do plugin:**
  - 2 branches remotos `claude/project-thread-*` com commits por integrar, ainda por decidir;
  - os branches locais `wip-seo-audit-website` (o WIP de SEO, feito para o layout antigo) e `correcoes-do-justclip` (já integrado).
