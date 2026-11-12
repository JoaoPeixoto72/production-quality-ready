# Runtime privacy and cookie audit (`audit-website`)

The GDPR (Regulation (EU) 2016/679) and the ePrivacy Directive (2002/58/EC)
require that no non-essential cookie or identifier is stored or sent before
free, specific, informed and explicit consent.

## 1. Golden rule: prior blocking (*consent prior to fire*)

No third-party script in these categories may run or open a connection before
the user affirmatively clicks "Accept":
- **Advertising and remarketing:** Meta Pixel, Google Ads, TikTok Pixel, LinkedIn Insight Tag, Criteo, Pinterest Tag.
- **Analytics and behavioural measurement:** Google Analytics 4 (without Consent Mode v2 set to deny storage), Hotjar, Microsoft Clarity, Mixpanel.
- **Content personalisation and affiliates:** Awin, Taboola, Outbrain.

## 2. Detection patterns

### 2.1 Static HTML and script analysis
- `<script src="...">` tags loaded straight in `<head>` or `<body>` without a consent manager (Cookiebot, Didomi, OneTrust, Klaro, Axeptio).
- Libraries such as `fbevents.js`, `analytics.js`, `gtag/js` or `clarity.js` that make network calls on first load.

### 2.2 Google Consent Mode v2
- A page using Google Consent Mode has, at the top of `<head>`:
  ```javascript
  gtag('consent', 'default', {
    'ad_storage': 'denied',
    'ad_user_data': 'denied',
    'ad_personalization': 'denied',
    'analytics_storage': 'denied'
  });
  ```
  Missing, or defaulting to `granted`, is a compliance breach.

### 2.3 Transparency and easy refusal
- The cookie banner **offers "Reject" or "Reject all" at the same hierarchy and visual level** as "Accept".
- No reject button hidden in a submenu in faded colours while "Accept" stands out.
- Preferences can be changed at any time (a floating icon or a footer link reopening the cookie settings).
