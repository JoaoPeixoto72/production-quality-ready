# Metodologia de Auditoria de Website (`audit-website`)

A auditoria de website do plugin `production-quality-ready` combina inspeção técnica determinística, avaliação qualitativa de conversão (CRO) e verificação em runtime de conformidade legal e privacidade.

Ao contrário de abordagens de consultoria que produzem "notas médias ponderadas" (ex.: 92/100), esta metodologia adota **Gates Binários Declarativos baseados em Severidade** (`BLOCKER`, `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`). Falhas graves em privacidade ou bloqueios de indexação bloqueiam a aprovação independentemente de quão rápida a página seja.

---

## 1. As 5 Questões Essenciais de Cada Apontamento

Cada finding emitido pela auditoria deve responder de forma acionável:
1. **O que está incorreto ou degradado?** (com citação exata de linha, seletor CSS ou URL).
2. **Quem e o que é afetado?** (visitantes mobile, utilizadores de tecnologias assistivas, tráfego orgânico, conformidade legal).
3. **Qual é o impacto real?** (técnico, comercial, reputacional ou sanção legal sob RGPD/ePrivacy).
4. **Qual é a prioridade de correção?** (classificação por severidade).
5. **Como se comprova a resolução?** (critério de aceitação observável em reteste).

---

## 2. Os 7 Pilares de Verificação

### Pilar 1: SEO Técnico & Rastreabilidade
- **Rastreio:** Acesso livre a bots legítimos no `robots.txt`, ausência de diretivas contraditórias no `X-Robots-Tag`.
- **Indexação:** Presença de `canonical` autorreferencial ou direcionado; metatags `robots` (`index, follow`).
- **Sitemap:** `sitemap.xml` válido, atualizado, acessível e sem URLs em erro (404/500).
- **Semântica:** Hierarquia de títulos única (`<h1>`), `title` (30 a 60 carateres), `meta description` (70 a 160 carateres).
- **Dados Estruturados:** JSON-LD válido sob `Schema.org` (WebSite, Organization, Product, Article).

### Pilar 2: Performance Web & Core Web Vitals (CWV)
- Avaliação baseada nas métricas do Google Chrome UX Report (CrUX) e Lighthouse:
  - **LCP (Largest Contentful Paint):** $\le 2.5\text{s}$ (75.º percentil).
  - **INP (Interaction to Next Paint):** $\le 200\text{ms}$.
  - **CLS (Cumulative Layout Shift):** $\le 0.1$.
  - **TTFB (Time to First Byte):** $\le 800\text{ms}$.
- Diagnóstico de recursos bloqueantes, compressão WebP/AVIF, lazy loading de imagens abaixo da dobra e ausência de imagens sem dimensões explícitas (`width`/`height`).

### Pilar 3: Privacidade & Bloqueio Prévio de Cookies (ePrivacy / RGPD)
- **Bloqueio Prévio (*Consent Prior to Fire*):** Proibição estrita de disparar trackers de marketing/publicidade (Meta Pixel, Google Ads, TikTok, Criteo, etc.) antes de o utilizador manifestar consentimento positivo no banner de cookies.
- **Mecanismo de Consentimento:** Presença de CMP (Consent Management Platform) ou banner com opção de recusa no mesmo nível visual da aceitação.
- **Transparência:** Link visível para a Política de Privacidade e Política de Cookies.

### Pilar 4: Web Analytics & Qualidade dos Dados
- **Configuração de Tags:** Identificadores válidos de GTM (`GTM-XXXXXX`) e GA4 (`G-XXXXXX`).
- **Deduplicação:** Verificação de ausência de snippets duplicados no mesmo documento.
- **Proteção de PII:** Garantia de que parâmetros de URL (`email`, `user`, `cpf`, `phone`) não são transmitidos para ferramentas de analytics externas.
- **Eventos Críticos:** `dataLayer` inicializado antes das tags dependentes.

### Pilar 5: CRO & Eficácia de Conversão
- **Proposta de Valor:** Clareza do benefício principal acima da dobra (*above the fold*).
- **Call-to-Action (CTA):** Botão de ação primário visível, com contraste forte e texto orientado a benefício.
- **Fricção de Formulários:** Minimização de campos obrigatórios (idealmente $\le 5$ campos para lead generation); validação e feedback inline; atributos `autocomplete` standard.
- **Ausência de Dark Patterns:** Proibição de caixas de consentimento comercial pré-selecionadas (*pre-ticked checkboxes*).

### Pilar 6: Saúde de Links & Ativos (Spider Crawler)
- **Varredura de Âncoras:** Deteção de links internos quebrados (`404 Not Found`, `500 Server Error`).
- **Loops e Redirecionamentos:** Ausência de cadeias de redirecionamento excessivas ($> 2$ saltos) e loops infinitos.
- **Ativos Multimédia:** Imagens com caminhos relativos ou absolutos inválidos.

### Pilar 7: Acessibilidade Pública (WCAG 2.2 AA)
- **Navegação por Teclado:** Foco visível (`:focus-visible`) nos controlos da montra e menus.
- **Semântica Assistiva:** Imagens com `alt` significativo; botões só-ícone com `aria-label`; formulários com `<label for="...">`.
- **Língua do Documento:** Atributo `lang` declarado na tag `<html>`.

---

## 3. Escala de Severidade

| Severidade | Critério no Website | Exemplo |
| :--- | :--- | :--- |
| `BLOCKER` | Violação legal grave, quebra total de conversão ou bloqueio de indexação global. | `noindex` na homepage; trackers de publicidade a disparar sem consentimento; checkout/formulário inoperacional. |
| `CRITICAL` | Prejuízo severo de SEO, dados corrompidos ou barreira intransponível de acessibilidade. | LCP $> 4\text{s}$; sitemap com centenas de 404s; botão de compra inacessível por teclado; PII vazada no URL. |
| `HIGH` | Fricção comercial expressiva, perda mensurável de tráfego orgânico ou falhas de tags. | Snippet de GA4 duplicado; formulário com 12 campos obrigatórios sem autocomplete; ausência de `canonical`. |
| `MEDIUM` | Defeito localizado com alternativa existente. | Título com 85 carateres (truncado); imagens sem dimensões explícitas; link quebrado em página secundária. |
| `LOW` | Oportunidade de otimização estética ou menor. | Meta description ligeiramente curta; ausência de tag Open Graph secundária. |
| `INFO` | Observação de boas práticas sem defeito direto. | Sugestão de adoção de novos esquemas de dados estruturados. |
