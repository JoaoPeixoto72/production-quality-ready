# Auditoria de Privacidade e Cookies em Runtime (`audit-website`)

A conformidade com o RGPD (Regulamento Geral sobre a Proteção de Dados - Regulamento UE 2016/679) e com a Diretiva ePrivacy (Diretiva 2002/58/CE) exige que nenhum cookie ou identificador não essencial seja gravado ou transmitido antes de consentimento livre, específico, informado e explícito.

---

## 1. Regra de Ouro: Bloqueio Prévio (*Consent Prior to Fire*)

Nenhum script de terceiros pertencente às seguintes categorias pode executar ou estabelecer ligação antes de o utilizador clicar afirmativamente em "Aceitar":
- **Publicidade e Remarketing:** Meta Pixel, Google Ads, TikTok Pixel, LinkedIn Insight Tag, Criteo, Pinterest Tag.
- **Analytics e Medição Comportamental:** Google Analytics 4 (sem Consent Mode v2 configurado para negar storage), Hotjar, Microsoft Clarity, Mixpanel.
- **Personalização de Conteúdo e Afiliados:** Awin, Taboola, Outbrain.

---

## 2. Padrões de Deteção na Auditoria

### 2.1 Análise Estática de HTML e Scripts
- Deteção de tags `<script src="...">` carregadas diretamente no `<head>` ou `<body>` sem estarem envelopadas por um gestor de consentimento (ex.: Cookiebot, Didomi, OneTrust, Klaro, Axeptio).
- Deteção de bibliotecas como `fbevents.js`, `analytics.js`, `gtag/js` ou `clarity.js` que iniciem chamadas de rede no carregamento inicial do documento.

### 2.2 Verificação do Consent Mode v2 (Google)
- Se a página utiliza o Google Consent Mode, deve existir no topo do `<head>` a instrução:
  ```javascript
  gtag('consent', 'default', {
    'ad_storage': 'denied',
    'ad_user_data': 'denied',
    'ad_personalization': 'denied',
    'analytics_storage': 'denied'
  });
  ```
  Se este comando estiver em falta ou se os valores por omissão forem `granted`, constitui violação de conformidade.

### 2.3 Transparência e Facilidade de Recusa
- O banner de cookies **deve disponibilizar um botão de "Rejeitar" ou "Recusar Todos" no mesmo nível hierárquico e visual** do botão "Aceitar".
- Não são permitidos botões de rejeição escondidos dentro de submenus com cores esbatidas enquanto o botão "Aceitar" está em destaque.
- Acesso contínuo para alterar as preferências (ex.: ícone flutuante ou link no rodapé para reabrir as configurações de cookies).
