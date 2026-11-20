# SEO Audit v1 — Core Checklist

## Crawling / Indexing
- [ ] `robots.txt` present, valid, does not accidentally disallow the site
- [ ] A `5xx` on `robots.txt` is treated as critical (compliant crawlers read it as "disallow all")
- [ ] `sitemap.xml` present, valid XML, referenced in `robots.txt`
- [ ] Sitemap under 50 000 URLs and 50 MB uncompressed
- [ ] Sampled URLs from sitemap return 200
- [ ] No accidental `noindex` on production — served in the **raw HTML**, not removed by JS (Google may honor a raw-HTML `noindex` even if JS removes it)
- [ ] Canonicals present, self-consistent, no chains — and identical in raw HTML and JS-rendered output
- [ ] Critical SEO elements (title, description, canonical, robots, JSON-LD) are in the initial server HTML, not injected only by JS
- [ ] Pagination uses crawlable `<a href>` URLs (Google no longer uses `rel=next/prev`); load-more/infinite scroll sit behind paginated URLs
- [ ] IndexNow implemented where Bing/Yandex/Naver matter (not Google)

## Head essentials (per page)
- [ ] `<title>` present, 30–60 char
- [ ] `<meta name="description">` 70–160 char
- [ ] Open Graph (`og:title`, `og:description`, `og:image`)
- [ ] Twitter Card
- [ ] `<link rel="canonical">`
- [ ] Exactly one `<h1>`
- [ ] `lang` on `<html>`

## Structured data
- [ ] JSON-LD parses
- [ ] Types exist on Schema.org
- [ ] No deprecated types treated as rich-result vehicles (HowTo, FAQPage for SERP)
- [ ] Required fields present per type
- [ ] No claim that a schema type improves LLM citation

## Core Web Vitals
- [ ] LCP good on mobile (≤ 2.5 s)
- [ ] INP good on mobile (≤ 200 ms) — INP replaced FID in March 2024; never reference FID
- [ ] CLS good (≤ 0.1)
- [ ] Field data (CrUX) when available; a lab-only number is `heuristic`, not a critical pass

## Rendering
- [ ] Meaningful content present in server HTML (not only after JS execution)
- [ ] Non-200 pages carry no JS-injected SEO elements (Google does not render JS on non-200)
- [ ] Client-only SPA flagged as heuristic risk for crawlers that do not render JS

## Mobile & page experience
- [ ] Mobile/desktop content parity: equivalent primary content, robots meta, titles, structured data
- [ ] No intrusive interstitials (full-page popups, standalone consent redirects) or excessive ad density
- [ ] Key content visible on load, not behind tabs/accordions or scroll-hijacked

## Security / platform
- [ ] HTTPS reachable
- [ ] `http://` redirects to `https://`
- [ ] HSTS present
- [ ] No mixed content
- [ ] No back-button hijacking via `history.pushState`/`replaceState` (spam-policy violation)

## International (when applicable)
- [ ] `hreflang` links are reciprocal
- [ ] `x-default` present where appropriate

## GEO / AEO
- [ ] Robots policy for each AI crawler is an explicit decision — and the claim is on the right bot (`references/seo-ai-crawlers.md`)
- [ ] Server HTML contains the answer to the primary question (many AI crawlers do not render JS)
- [ ] `llms.txt` presence reported; it is informational (Google does not use it)

## Content hygiene
- [ ] No duplicated titles / H1s across the sample
- [ ] Non-empty body copy, meaningful length for the page type
- [ ] Internal links do not 404
