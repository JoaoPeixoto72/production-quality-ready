# Website audit methodology (`audit-website`)

The website audit combines deterministic technical inspection, qualitative
conversion review (CRO) and runtime verification of legal and privacy
compliance.

Instead of weighted average scores (92/100), it uses **declarative binary gates
by severity** (`BLOCKER`, `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`). Serious
privacy failures or indexing blocks stop approval however fast the page is.

## 1. The 5 questions every finding answers

1. **What is wrong or degraded?** (exact line, CSS selector or URL).
2. **Who and what is affected?** (mobile visitors, assistive-technology users, organic traffic, legal compliance).
3. **What is the real impact?** (technical, commercial, reputational, or a GDPR/ePrivacy sanction).
4. **What is the fix priority?** (severity).
5. **How is the fix proven?** (an acceptance criterion observable on retest).

## 2. The 7 verification pillars

### Pillar 1: technical SEO & crawlability
- **Crawling:** legitimate bots allowed in `robots.txt`, no contradictory `X-Robots-Tag` directives.
- **Indexing:** self-referencing or directed `canonical`; `robots` meta tags (`index, follow`).
- **Sitemap:** a valid, current, reachable `sitemap.xml` with no error URLs (404/500).
- **Semantics:** a single `<h1>`, `title` (30 to 60 characters), `meta description` (70 to 160 characters).
- **Structured data:** valid `Schema.org` JSON-LD (WebSite, Organization, Product, Article).

### Pillar 2: web performance & Core Web Vitals (CWV)
- From the Chrome UX Report (CrUX) and Lighthouse:
  - **LCP (Largest Contentful Paint):** $\le 2.5\text{s}$ (75th percentile).
  - **INP (Interaction to Next Paint):** $\le 200\text{ms}$.
  - **CLS (Cumulative Layout Shift):** $\le 0.1$.
  - **TTFB (Time to First Byte):** $\le 800\text{ms}$.
- Render-blocking resources, WebP/AVIF compression, lazy loading below the fold, and images without explicit `width`/`height`.

### Pillar 3: privacy & prior cookie blocking (ePrivacy / GDPR)
- **Prior blocking (*consent prior to fire*):** no marketing/advertising tracker (Meta Pixel, Google Ads, TikTok, Criteo…) fires before the user consents in the cookie banner.
- **Consent mechanism:** a CMP (Consent Management Platform) or banner whose reject option sits at the same visual level as accept.
- **Transparency:** a visible link to the privacy and cookie policies.

### Pillar 4: web analytics & data quality
- **Tag configuration:** valid GTM (`GTM-XXXXXX`) and GA4 (`G-XXXXXX`) IDs.
- **Deduplication:** no duplicate snippets in one document.
- **PII protection:** URL parameters (`email`, `user`, `cpf`, `phone`) never reach external analytics.
- **Critical events:** `dataLayer` initialised before the tags that depend on it.

### Pillar 5: CRO & conversion
- **Value proposition:** the main benefit is clear above the fold.
- **Call to action (CTA):** a visible primary action, strong contrast, benefit-driven text.
- **Form friction:** few required fields (ideally $\le 5$ for lead generation); inline validation and feedback; standard `autocomplete`.
- **No dark patterns:** no pre-ticked commercial consent checkboxes.

### Pillar 6: link & asset health (spider)
- **Anchor sweep:** broken internal links (`404 Not Found`, `500 Server Error`).
- **Loops and redirects:** no redirect chains over 2 hops, no infinite loops.
- **Media assets:** images with invalid relative or absolute paths.

### Pillar 7: public accessibility (WCAG 2.2 AA)
- **Keyboard navigation:** visible focus (`:focus-visible`) on storefront controls and menus.
- **Assistive semantics:** meaningful `alt`; icon-only buttons with `aria-label`; forms with `<label for="...">`.
- **Document language:** `lang` declared on `<html>`.

## 3. Severity scale

| Severity | Website criterion | Example |
| :--- | :--- | :--- |
| `BLOCKER` | Serious legal breach, conversion fully broken, or global indexing block. | `noindex` on the home page; ad trackers firing without consent; checkout/form not working. |
| `CRITICAL` | Severe SEO damage, corrupted data, or an impassable accessibility barrier. | LCP $> 4\text{s}$; sitemap with hundreds of 404s; buy button unreachable by keyboard; PII leaked in the URL. |
| `HIGH` | Marked commercial friction, measurable organic traffic loss, or tag failures. | Duplicate GA4 snippet; form with 12 required fields and no autocomplete; no `canonical`. |
| `MEDIUM` | Localised defect with an existing alternative. | 85-character title (truncated); images without explicit size; broken link on a secondary page. |
| `LOW` | Minor or aesthetic optimisation. | Meta description slightly short; a secondary Open Graph tag missing. |
| `INFO` | Good-practice note with no direct defect. | Suggesting new structured-data schemas. |
