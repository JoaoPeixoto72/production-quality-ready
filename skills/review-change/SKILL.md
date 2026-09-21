---
name: review-change
description: "Review a change before calling it done. Enforces local invariants combined with the plugin's Universal Adversarial Matrix (concurrency, input tampering, IDOR, webhooks/retries, XSS, WCAG AA, DB immutability) and runs proof commands. Universal contract; each project supplies adapter with invariants and proof commands. Use after changing code, before close-work. Do NOT use to audit whole app — that's audit-app. Do NOT use to open — that's start-work."
contract: CONTRACTS.md
evidence-schema: "1.3.x"
requires-adapter: true
adapter-contract: adapter-contracts/review-change.md
version: 1.1.0
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---

# review-change

Universal contract for reviewing a change before commit. This is the
last honest checkpoint between "code written" and "close the task"; when
it skips, defects that live inside the change (broken invariants,
architectural drift, missed retry, unsafe input) reach the audit as
noise you now have to sort back out.

## Regra Fundacional: Testes a passar são o MÍNIMO, nunca a prova de aprovação

Um conjunto de testes unitários a 100% prova apenas que os cenários que foram
escritos passaram. Não prova ausência de falhas em concorrência, omissão de
parâmetros ou falhas parciais de rede.
A revisão DEVE ser conduzida com postura **adversarial e destrutiva**, assumindo
que clientes e rede são hostis.

## A Matriz Adversarial Universal (7 Eixos Obrigatórios)

Toda a revisão de código neste plugin DEVE auditar e justificar explicitamente
os seguintes 7 eixos universais de qualidade de topo:

### 1. Concorrência e Double-Click (Anti-Race Condition) · [code-review-runtime]
- **Regra:** NUNCA ler da base de dados (`SELECT`) e decidir a escrita depois
  (`UPDATE`/`INSERT`) em passos separados (Time-of-Check to Time-of-Use — TOCTOU).
- **Cenário de Teste:** O que acontece se o utilizador fizer duplo clique no
  botão em 50ms com rede móvel instável, ou se dois clientes/trabalhadores
  submeterem a mesma ação no mesmo milissegundo?
- **Padrão Exigido:** Operações atómicas no motor de dados (ex.: `CASE WHEN EXISTS (...)`,
  `INSERT ... WHERE NOT EXISTS (...)`, transações atómicas em lote ou índices
  únicos parciais). O segundo pedido deve convergir sem corromper estado, duplicar
  cobranças ou gerar múltiplos prémios/vouchers.

### 2. Omissão de Parâmetros e Input Tampering · [security-audit]
- **Regra:** NUNCA confiar que o frontend enviou o que devia. A validação do
  frontend é cosmética de UX, não segurança.
- **Cenário de Teste:** O que acontece se uma chamada de API (via cURL/Postman)
  omitir propositadamente um parâmetro ou enviar `null`, `undefined` ou string vazia?
- **Padrão Exigido:** Parâmetros de validação (ex.: coordenadas de geofence,
  tokens de validação, identificadores de cliente) DEVEM ser validados no
  backend. Se omitidos, recusa com `400 Bad Request` ou `403 Forbidden`,
  NUNCA saltando a verificação.

### 3. Isolamento Multi-Tenant e Anti-IDOR Estrito · [security-audit, code-review-contract]
- **Regra:** Todo o acesso a recursos privados (dados de clientes, catálogo,
  faturação, mesas, eventos) DEVE ser escopado pela sessão autenticada.
- **Cenário de Teste:** Se o utilizador da Conta A alterar manualmente o ID no
  URL ou no payload JSON para o ID da Conta B, o que acontece?
- **Padrão Exigido:** Todas as queries SQL/ORM a recursos privados contêm
  `WHERE id = ? AND tenant_id = ?` (ou equivalente de posse). Falhas de posse
  devolvem sempre `404 Not Found` (para impedir enumeração). Áreas financeiras
  ou contratuais restringem-se a permissões de proprietário (`role = 'owner'`).

### 4. Webhooks, Retries e Falhas Parciais (Chaos Engineering) · [code-review-contract]
- **Regra:** Em integrações assíncronas (Stripe, gateways, faturação fiscal, email),
  falhas temporárias não podem deixar o utilizador sem acesso nem emitir dados
  duplicados.
- **Cenário de Teste:** Se a base de dados ou a API externa falhar a meio do
  processamento do webhook, como responde o servidor?
- **Padrão Exigido:**
  - Webhooks de pagamento devolvem `500` perante falha interna de processamento
    para forçar a plataforma emissora a repetir a entrega com backoff exponencial;
    registam eventos em tabela de deduplicação por `event_id`. Devolvem `200`
    apenas quando processados com sucesso.
  - Faturação externa e emissão fiscal incluem `Idempotency-Key` estável para que
    retries de rede nunca gerem documentos fiscais duplicados.
  - O livro de créditos/transações distingue erros de chave única (`isUniqueViolation`)
    de falhas reais de infraestrutura (que devem propagar/re-tentar).

### 5. Sanitização em Fronteiras e Prevenção de XSS/Injeção · [security-audit]
- **Regra:** Dados controlados pelo utilizador nunca podem ser injetados em
  contextos interpretados (HTML, JS, SQL dinâmico) sem escape neutro.
- **Cenário de Teste:** O que acontece se uma string contiver `</script><script>alert(1)</script>`
  ou carateres de terminação de bloco?
- **Padrão Exigido:** Qualquer serialização dentro de tags `<script>` em SSR DEVE
  usar `safeJson()` (escape Unicode de `<`, `>`, `&`). Cabeçalhos CSP devem incluir
  nonces criptográficos por resposta (`'nonce-...'`) em `script-src`.

### 6. Acessibilidade Real (WCAG 2.2 AA) e Navegação por Teclado · [design-pro]
- **Regra:** A aplicação tem de ser navegável por utilizadores de teclado e
  leitores de ecrã com contraste perceptível.
- **Cenário de Teste:** Se desligar o rato e navegar exclusivamente com Tab / Shift+Tab,
  o foco é sempre visível? O leitor de ecrã sabe que um modal abriu?
- **Padrão Exigido:**
  - `:focus-visible` visível em todos os controlos interativos; proibido `outline: none` global.
  - Modais com semântica `role="dialog"`, `aria-modal="true"`, `aria-label`,
    captura de foco (focus trap) e devolução de foco ao elemento original ao fechar.
  - Botões só-ícone com `aria-label` explícito; `<label>` associadas com `for`.
  - Contraste de cor verificado com rácio mínimo matemático de 4.5:1 (WCAG AA).

### 7. Determinismo e Imutabilidade de Esquema de Base de Dados · [reliability-audit]
- **Regra:** NUNCA editar ficheiros de migração de base de dados já publicados ou aplicados.
- **Cenário de Teste:** O que acontece se uma migração antiga for alterada localmente?
- **Padrão Exigido:** Migrações publicadas são verificadas por checksum SHA-256
  com quebras de linha normalizadas (LF canónico). Novas alterações de esquema
  constituem SEMPRE uma nova migração sequencial versionada.

---

## Ordem de Execução do `review-change`

1. **Ler o diff completo.** Nada mais antes disto (`git diff`).
2. **Executar cada Invariante Local.** O adaptador do projeto enumera os
   invariantes específicos deste produto e respetivos exemplos concretos.
3. **Executar a Matriz Adversarial Universal.** Avaliar o diff contra os 7 eixos
   acima. Se algum for violado, a alteração está BLOQUEADA.
4. **Executar os Comandos de Prova.** Correr o comando declarado pelo adaptador
   (build, linter, typecheck, testes, migrações) e reportar o resultado com número + HEAD.

---

## Contract for the local adapter

O adaptador local DEVE fornecer:
1. `This project's invariants` — enumerados com os exemplos concretos que motivaram
   cada um no histórico deste repositório.
2. `Proof command` — comando exato de validação pré-conclusão.
3. Concretizações específicas de projeto que instanciem a matriz universal.

Ver `adapter-contracts/review-change.md`.
