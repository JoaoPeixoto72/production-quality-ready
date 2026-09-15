# SEO Audit v1 — Core Checklist

## Crawling / Indexing
- [ ] `robots.txt` present, valid, does not accidentally disallow the site
- [ ] `sitemap.xml` present, valid XML, referenced in `robots.txt`
- [ ] Sitemap under 50 000 URLs and 50 MB uncompressed
- [ ] Sampled URLs from sitemap return 200
- [ ] No accidental `noindex` on production
- [ ] Canonicals present, self-consistent, no chains

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

## Core Web Vitals (via PSI when a key is provided)
- [ ] LCP good on mobile (≤ 2.5 s)
- [ ] INP good on mobile (≤ 200 ms) — INP replaced FID in March 2024
- [ ] CLS good (≤ 0.1)

## Rendering
- [ ] Meaningful content present in server HTML (not only after JS execution)
- [ ] Client-only SPA flagged as heuristic risk for LLM crawlers

## Security / platform
- [ ] HTTPS reachable
- [ ] `http://` redirects to `https://`
- [ ] HSTS present
- [ ] No mixed content

## International (when applicable)
- [ ] `hreflang` links are reciprocal
- [ ] `x-default` present where appropriate

## GEO / AEO
- [ ] Robots policy for LLM crawlers is an explicit decision (allow or block)
- [ ] Server HTML contains the answer to the primary question (LLM crawlers don't reliably render JS)
- [ ] `llms.txt` present is informational (Google does not use it; some LLMs may)

## Content hygiene
- [ ] No duplicated titles / H1s across the sample
- [ ] Non-empty body copy, meaningful length for the page type
- [ ] Internal links do not 404
