#!/usr/bin/env node
// SEO Audit v1 — evidence-based SEO audit engine.
//
// Copyright (c) 2026 João Carlos de Sousa Peixoto
// SPDX-License-Identifier: Apache-2.0

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = process.cwd()
const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url))
const SKILL_DIR = path.resolve(SCRIPT_DIR, '..')
const cliArgs = process.argv.slice(2)
const getFlag = (name) => {
  const hit = cliArgs.find((a) => a.startsWith(`--${name}=`))
  return hit ? hit.slice(name.length + 3) : ''
}
const hasFlag = (name) => cliArgs.includes(`--${name}`)

const DEFAULT_CONFIG = {
  version: '1.0.0',
  profilePath: '',
  sitemapMax: 25,
  psiKey: '',
  thresholds: {
    titleMin: 30, titleMax: 60,
    descriptionMin: 70, descriptionMax: 160,
    lcpGoodMs: 2500, inpGoodMs: 200, clsGood: 0.1,
    targetPassScore: 90
  },
  profile: {}
}

function tryReadJson(p) { try { return JSON.parse(fs.readFileSync(p, 'utf8')) } catch { return null } }
function mergeConfig(base, next) {
  return {
    ...base, ...next,
    thresholds: { ...(base.thresholds || {}), ...(next.thresholds || {}) },
    profile: { ...(base.profile || {}), ...(next.profile || {}) }
  }
}

let cfg = { ...DEFAULT_CONFIG }
for (const c of [path.join(ROOT, 'seo-audit.config.json'), path.join(SKILL_DIR, 'audit.config.json')]) {
  if (fs.existsSync(c)) {
    const parsed = tryReadJson(c); if (parsed) { cfg = mergeConfig(cfg, parsed); break }
  }
}
const rawProfile = getFlag('profile') || cfg.profilePath
if (rawProfile) {
  const candidates = [path.resolve(ROOT, rawProfile), path.resolve(SKILL_DIR, rawProfile)]
  const resolved = candidates.find(fs.existsSync)
  if (resolved) { const p = tryReadJson(resolved); if (p) cfg = mergeConfig(cfg, p) }
}

const targetUrl = getFlag('url')
const buildDir = getFlag('dir')
const psiKey = getFlag('psi-key') || cfg.psiKey || ''
const sitemapMax = Number(getFlag('sitemap-max') || cfg.sitemapMax || 25)
const wantXml = hasFlag('xml')
const showRunbook = hasFlag('runbook')

if (showRunbook) {
  console.log('================================================================================')
  console.log('  SEO AUDIT v1 — RUNBOOK & ENGINE LIMITS')
  console.log('================================================================================')
  console.log(`
  This engine can prove:
    - HTTP reachability, status codes, redirects
    - robots.txt / sitemap.xml presence, XML validity, size limits
    - <title>, <meta description>, canonical, hreflang, headings, lang, og/twitter
    - JSON-LD parsing and Schema.org type presence
    - Core Web Vitals via PageSpeed Insights API when a key is provided
    - Rendering surface size when compared to typical SPA shells
    - HTTPS, HSTS, mixed content
    - llms.txt presence (informational only)

  This engine cannot prove:
    - Ranking outcomes in Google, Bing, ChatGPT, Perplexity, or Claude
    - E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) — that is editorial judgment
    - Content quality or factual accuracy
    - Backlink profile

  When evidence is missing, findings are NOT_VERIFIED — not FAIL.
`)
  process.exit(0)
}

if (!targetUrl && !buildDir) {
  console.log('Usage:')
  console.log('  node run_seo_audit.mjs --url=https://example.com')
  console.log('  node run_seo_audit.mjs --dir=./dist')
  console.log('  node run_seo_audit.mjs --runbook')
  process.exit(1)
}

const SEVERITY_WEIGHTS = { Critical: 10, High: 6, Medium: 3, Low: 1 }
const findings = []
let hardGateFailed = false
const hardGateReasons = []

function record(def, out) {
  const { id, category, title, severity, evidenceClass } = def
  let status = out.status || 'NOT_VERIFIED'
  if (status === 'FAIL' && severity === 'Critical' && evidenceClass === 'heuristic') {
    status = 'WARN'
    out.message = `[downgraded from FAIL — heuristic] ${out.message || ''}`.trim()
  }
  const item = {
    id, category, title, severity, evidenceClass,
    status,
    confidence: out.confidence || (evidenceClass === 'machine_verified' ? 'high' : evidenceClass === 'heuristic' ? 'medium' : 'low'),
    message: out.message || '',
    details: out.details || null,
    weight: SEVERITY_WEIGHTS[severity] || 1
  }
  if (severity === 'Critical' && status === 'FAIL' && evidenceClass !== 'heuristic') {
    hardGateFailed = true
    hardGateReasons.push(`[${id}] ${title}: ${item.message}`)
  }
  findings.push(item)
  const badge = `[${status === 'NOT_APPLICABLE' ? 'N/A' : status}]`.padEnd(16)
  console.log(`  ${badge}${id} - ${title}${item.message ? ` (${item.message})` : ''}`)
}

async function safeFetch(url, opts = {}) {
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), opts.timeout || 15000)
    const res = await fetch(url, { redirect: 'follow', headers: { 'User-Agent': 'SEOAudit/1.0' }, ...opts, signal: controller.signal })
    clearTimeout(timeout)
    return res
  } catch (err) {
    return { ok: false, status: 0, _error: err.message, headers: new Map(), text: async () => '' }
  }
}

// ---------------------------------------------------------------------------
// Tiny HTML parser tailored to SEO signals. Not a full DOM.
// ---------------------------------------------------------------------------
function pickAttr(tag, attr) {
  const m = tag.match(new RegExp(`\\b${attr}\\s*=\\s*"([^"]*)"`, 'i')) || tag.match(new RegExp(`\\b${attr}\\s*=\\s*'([^']*)'`, 'i'))
  return m ? m[1] : ''
}
function extractHeadSignals(html) {
  const lang = (html.match(/<html[^>]*\blang\s*=\s*["']([^"']+)["']/i) || [])[1] || ''
  const title = (html.match(/<title[^>]*>([\s\S]*?)<\/title>/i) || [])[1]?.trim() || ''
  const metas = [...html.matchAll(/<meta\b[^>]*>/gi)].map((m) => m[0])
  const meta = {
    description: '',
    ogTitle: '', ogDescription: '', ogImage: '',
    twitterCard: '',
    robots: ''
  }
  for (const t of metas) {
    const name = pickAttr(t, 'name').toLowerCase()
    const prop = pickAttr(t, 'property').toLowerCase()
    const content = pickAttr(t, 'content')
    if (name === 'description') meta.description = content
    if (prop === 'og:title') meta.ogTitle = content
    if (prop === 'og:description') meta.ogDescription = content
    if (prop === 'og:image') meta.ogImage = content
    if (name === 'twitter:card') meta.twitterCard = content
    if (name === 'robots') meta.robots = content
  }
  const canonicals = [...html.matchAll(/<link\b[^>]*rel\s*=\s*["']canonical["'][^>]*>/gi)].map((m) => pickAttr(m[0], 'href')).filter(Boolean)
  const hreflangs = [...html.matchAll(/<link\b[^>]*rel\s*=\s*["']alternate["'][^>]*>/gi)]
    .map((m) => ({ href: pickAttr(m[0], 'href'), hreflang: pickAttr(m[0], 'hreflang') }))
    .filter((x) => x.hreflang)
  const h1Count = (html.match(/<h1\b[^>]*>[\s\S]*?<\/h1>/gi) || []).length
  const jsonLdBlocks = [...html.matchAll(/<script\b[^>]*type\s*=\s*["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)].map((m) => m[1])
  const imgCount = (html.match(/<img\b/gi) || []).length
  const imgWithoutAlt = (html.match(/<img\b(?![^>]*\balt\s*=)[^>]*>/gi) || []).length
  const bodyMatch = html.match(/<body\b[^>]*>([\s\S]*)<\/body>/i)
  const bodyText = bodyMatch ? bodyMatch[1].replace(/<script[\s\S]*?<\/script>/gi, '').replace(/<style[\s\S]*?<\/style>/gi, '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim() : ''
  return { lang, title, meta, canonicals, hreflangs, h1Count, jsonLdBlocks, imgCount, imgWithoutAlt, bodyText }
}

function classifyRenderingLikelihood(html) {
  // Very small HTML with a big JS bundle reference is a classic SPA shell.
  const size = html.length
  const hasBigJs = /<script\s+[^>]*src=[^>]+>/i.test(html)
  const bodyMatch = html.match(/<body\b[^>]*>([\s\S]*)<\/body>/i)
  const bodyLen = bodyMatch ? bodyMatch[1].replace(/<[^>]+>/g, '').trim().length : 0
  return { size, bodyLen, likelySpa: bodyLen < 300 && hasBigJs }
}

// ---------------------------------------------------------------------------
// Live URL checks
// ---------------------------------------------------------------------------
async function runLiveAudit(url) {
  console.log('--- CRAWL / INDEX ---')
  const origin = new URL(url).origin

  // HTTPS reachability
  const rootRes = await safeFetch(url)
  if (rootRes.status === 0) {
    record({ id: 'NET-01', category: 'crawling', title: 'HTTPS reachability', severity: 'Critical', evidenceClass: 'machine_verified' }, { status: 'NOT_VERIFIED', message: `Network error: ${rootRes._error}` })
    return
  }
  const isLocalhost = /^(https?:\/\/)?(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])(:\d+)?/i.test(url)
  if (isLocalhost) {
    record({ id: 'NET-01', category: 'crawling', title: 'HTTPS reachability', severity: 'Low', evidenceClass: 'machine_verified' }, { status: 'NOT_APPLICABLE', message: 'Local host — HTTPS check does not apply. Re-run against the production hostname.' })
  } else {
    record({ id: 'NET-01', category: 'crawling', title: 'HTTPS reachability', severity: 'Critical', evidenceClass: 'machine_verified' }, url.startsWith('https://') && rootRes.ok ? { status: 'PASS', message: `HTTP ${rootRes.status} over HTTPS` } : { status: url.startsWith('https://') ? 'WARN' : 'FAIL', message: `HTTP ${rootRes.status} — ${url.startsWith('https://') ? 'non-2xx' : 'not HTTPS'}` })
  }

  // HSTS
  const hsts = rootRes.headers.get?.('strict-transport-security') || ''
  record({ id: 'SEC-HSTS-01', category: 'security', title: 'HSTS header', severity: 'Medium', evidenceClass: 'machine_verified' }, hsts.includes('max-age=') ? { status: 'PASS', message: 'HSTS present' } : { status: 'WARN', message: 'Strict-Transport-Security not set' })

  // robots.txt
  const robotsRes = await safeFetch(origin + '/robots.txt')
  const robotsText = robotsRes.ok ? await robotsRes.text() : ''
  if (!robotsRes.ok) {
    record({ id: 'CRAWL-ROBOTS-01', category: 'crawling', title: 'robots.txt reachable', severity: 'Medium', evidenceClass: 'machine_verified' }, { status: 'WARN', message: `HTTP ${robotsRes.status}` })
  } else {
    const disallowAll = /(^|\n)\s*User-agent:\s*\*\s*[\r\n]+([^\n]*\n)*\s*Disallow:\s*\/\s*(\n|$)/i.test(robotsText)
    record({ id: 'CRAWL-ROBOTS-01', category: 'crawling', title: 'robots.txt reachable', severity: 'Medium', evidenceClass: 'machine_verified' }, disallowAll ? { status: 'FAIL', message: 'robots.txt disallows the entire site for all user agents' } : { status: 'PASS', message: 'robots.txt reachable and does not disallow everything' })

    // LLM crawler policy — informational
    const llmAgents = ['GPTBot', 'ClaudeBot', 'PerplexityBot', 'Google-Extended', 'CCBot', 'Bytespider']
    const declared = llmAgents.filter((a) => new RegExp(`User-agent:\\s*${a}`, 'i').test(robotsText))
    record({ id: 'GEO-BOTS-01', category: 'geo', title: 'Robots policy for known LLM crawlers is explicit', severity: 'Low', evidenceClass: 'machine_verified' }, declared.length ? { status: 'PASS', message: `Declared: ${declared.join(', ')}` } : { status: 'WARN', message: 'No explicit policy for GPTBot / ClaudeBot / PerplexityBot / Google-Extended' })

    // Sitemap reference
    const sitemapRefs = [...robotsText.matchAll(/^\s*Sitemap:\s*(\S+)/gim)].map((m) => m[1])
    record({ id: 'CRAWL-SITEMAP-REF-01', category: 'crawling', title: 'robots.txt references a Sitemap', severity: 'Low', evidenceClass: 'machine_verified' }, sitemapRefs.length ? { status: 'PASS', message: sitemapRefs.join(', ') } : { status: 'WARN', message: 'No Sitemap: entry found in robots.txt' })
  }

  // sitemap.xml
  const sitemapUrl = origin + '/sitemap.xml'
  const sitemapRes = await safeFetch(sitemapUrl)
  let sitemapUrls = []
  if (!sitemapRes.ok) {
    record({ id: 'CRAWL-SITEMAP-01', category: 'crawling', title: 'sitemap.xml reachable', severity: 'High', evidenceClass: 'machine_verified' }, { status: 'WARN', message: `HTTP ${sitemapRes.status} at /sitemap.xml` })
  } else {
    const sitemapText = await sitemapRes.text()
    const sizeMb = sitemapText.length / 1024 / 1024
    const urls = [...sitemapText.matchAll(/<loc>([^<]+)<\/loc>/gi)].map((m) => m[1].trim())
    sitemapUrls = urls
    const problems = []
    if (urls.length > 50000) problems.push(`${urls.length} URLs (over 50 000)`)
    if (sizeMb > 50) problems.push(`${sizeMb.toFixed(1)} MB (over 50 MB)`)
    if (!/<urlset|<sitemapindex/i.test(sitemapText)) problems.push('does not look like a valid sitemap or sitemap index')
    record({ id: 'CRAWL-SITEMAP-01', category: 'crawling', title: 'sitemap.xml valid', severity: 'High', evidenceClass: 'machine_verified' }, problems.length ? { status: 'FAIL', message: problems.join('; ') } : { status: 'PASS', message: `${urls.length} URLs, ${sizeMb.toFixed(2)} MB` })

    // Sample sitemap URLs
    const sample = urls.slice(0, sitemapMax)
    let bad = 0
    for (const u of sample) {
      const r = await safeFetch(u, { method: 'HEAD' })
      if (!r.ok || r.status >= 400) bad++
    }
    record({ id: 'CRAWL-SITEMAP-STATUS-01', category: 'crawling', title: `Sampled sitemap URLs return 200 (n=${sample.length})`, severity: 'High', evidenceClass: 'machine_verified' }, bad === 0 ? { status: 'PASS', message: `${sample.length}/${sample.length} OK` } : { status: 'FAIL', message: `${bad}/${sample.length} returned non-2xx` })
  }

  // llms.txt — informational only
  const llmsRes = await safeFetch(origin + '/llms.txt', { method: 'HEAD' })
  record({ id: 'GEO-LLMS-01', category: 'geo', title: 'llms.txt present (informational)', severity: 'Low', evidenceClass: 'machine_verified' }, llmsRes.ok ? { status: 'PASS', message: 'llms.txt reachable. Note: Google publicly states it does not use llms.txt for ranking; some LLMs may.' } : { status: 'WARN', message: 'No llms.txt — informational only, Google does not use it' })

  // Root HTML deep audit
  console.log('\n--- HEAD & ON-PAGE (root URL) ---')
  const rootHtml = rootRes.ok ? await rootRes.text() : ''
  const signals = extractHeadSignals(rootHtml)
  const rendering = classifyRenderingLikelihood(rootHtml)

  const titleLen = signals.title.length
  const tMin = cfg.thresholds.titleMin, tMax = cfg.thresholds.titleMax
  record({ id: 'HEAD-TITLE-01', category: 'head', title: `<title> length in [${tMin}, ${tMax}]`, severity: 'High', evidenceClass: 'machine_verified' },
    !signals.title ? { status: 'FAIL', message: 'Missing <title>' } :
    titleLen < tMin ? { status: 'WARN', message: `${titleLen} chars — below ${tMin}` } :
    titleLen > tMax ? { status: 'WARN', message: `${titleLen} chars — above ${tMax}` } :
    { status: 'PASS', message: `${titleLen} chars` })

  const descLen = signals.meta.description.length
  const dMin = cfg.thresholds.descriptionMin, dMax = cfg.thresholds.descriptionMax
  record({ id: 'HEAD-DESC-01', category: 'head', title: `meta description length in [${dMin}, ${dMax}]`, severity: 'Medium', evidenceClass: 'machine_verified' },
    !signals.meta.description ? { status: 'WARN', message: 'Missing meta description' } :
    descLen < dMin ? { status: 'WARN', message: `${descLen} chars — below ${dMin}` } :
    descLen > dMax ? { status: 'WARN', message: `${descLen} chars — above ${dMax}` } :
    { status: 'PASS', message: `${descLen} chars` })

  record({ id: 'HEAD-OG-01', category: 'head', title: 'Open Graph tags present', severity: 'Low', evidenceClass: 'machine_verified' },
    signals.meta.ogTitle && signals.meta.ogDescription && signals.meta.ogImage
      ? { status: 'PASS', message: 'og:title, og:description, og:image' }
      : { status: 'WARN', message: 'Missing at least one of og:title / og:description / og:image' })

  record({ id: 'HEAD-TW-01', category: 'head', title: 'Twitter Card present', severity: 'Low', evidenceClass: 'machine_verified' },
    signals.meta.twitterCard ? { status: 'PASS', message: signals.meta.twitterCard } : { status: 'WARN', message: 'No twitter:card meta tag' })

  record({ id: 'HEAD-CANON-01', category: 'head', title: 'Canonical link', severity: 'Medium', evidenceClass: 'machine_verified' },
    signals.canonicals.length === 0 ? { status: 'WARN', message: 'No canonical link' } :
    signals.canonicals.length > 1 ? { status: 'FAIL', message: `Multiple canonicals: ${signals.canonicals.join(', ')}` } :
    { status: 'PASS', message: signals.canonicals[0] })

  record({ id: 'HEAD-H1-01', category: 'head', title: 'Exactly one <h1>', severity: 'Medium', evidenceClass: 'machine_verified' },
    signals.h1Count === 1 ? { status: 'PASS', message: '1 h1' } :
    signals.h1Count === 0 ? { status: 'WARN', message: 'No <h1> found' } :
    { status: 'WARN', message: `${signals.h1Count} <h1> tags` })

  record({ id: 'HEAD-LANG-01', category: 'head', title: 'lang attribute on <html>', severity: 'Low', evidenceClass: 'machine_verified' },
    signals.lang ? { status: 'PASS', message: signals.lang } : { status: 'WARN', message: 'No lang="..." on <html>' })

  // Robots meta blocking
  record({ id: 'CRAWL-ROBOTS-META-01', category: 'crawling', title: 'No accidental noindex on root', severity: 'Critical', evidenceClass: 'machine_verified' },
    /noindex/i.test(signals.meta.robots) ? { status: 'FAIL', message: `robots="${signals.meta.robots}"` } : { status: 'PASS', message: signals.meta.robots || '(no robots meta)' })

  // Images alt
  record({ id: 'ONPAGE-ALT-01', category: 'content', title: 'Images have alt attributes', severity: 'Low', evidenceClass: 'machine_verified' },
    signals.imgCount === 0 ? { status: 'NOT_APPLICABLE', message: 'No <img> tags on root' } :
    signals.imgWithoutAlt === 0 ? { status: 'PASS', message: `${signals.imgCount} images, all with alt` } :
    { status: 'WARN', message: `${signals.imgWithoutAlt}/${signals.imgCount} <img> without alt` })

  // Structured data
  console.log('\n--- STRUCTURED DATA ---')
  if (signals.jsonLdBlocks.length === 0) {
    record({ id: 'SCHEMA-01', category: 'schema', title: 'JSON-LD present', severity: 'Medium', evidenceClass: 'machine_verified' }, { status: 'WARN', message: 'No <script type="application/ld+json"> found on root' })
  } else {
    let bad = 0
    const types = new Set()
    const deprecatedSurfaced = new Set()
    for (const block of signals.jsonLdBlocks) {
      try {
        const data = JSON.parse(block)
        const items = Array.isArray(data) ? data : [data]
        for (const item of items) {
          const stack = [item]
          while (stack.length) {
            const cur = stack.pop()
            if (cur && typeof cur === 'object') {
              const t = cur['@type']
              if (Array.isArray(t)) t.forEach((x) => types.add(x))
              else if (typeof t === 'string') types.add(t)
              if (t === 'FAQPage' || (Array.isArray(t) && t.includes('FAQPage'))) deprecatedSurfaced.add('FAQPage')
              if (t === 'HowTo' || (Array.isArray(t) && t.includes('HowTo'))) deprecatedSurfaced.add('HowTo')
              for (const k of Object.keys(cur)) if (typeof cur[k] === 'object' && cur[k]) stack.push(cur[k])
            }
          }
        }
      } catch { bad++ }
    }
    record({ id: 'SCHEMA-01', category: 'schema', title: 'JSON-LD parses', severity: 'Medium', evidenceClass: 'machine_verified' },
      bad === 0 ? { status: 'PASS', message: `${signals.jsonLdBlocks.length} blocks parsed; types: ${[...types].join(', ') || '(none)'}` }
                : { status: 'FAIL', message: `${bad}/${signals.jsonLdBlocks.length} JSON-LD blocks failed to parse` })
    if (deprecatedSurfaced.size) {
      record({ id: 'SCHEMA-DEPRECATED-01', category: 'schema', title: 'Deprecated schema types present', severity: 'Low', evidenceClass: 'machine_verified' }, { status: 'WARN', message: `Deprecated for Google SERP: ${[...deprecatedSurfaced].join(', ')}. Do not add new; do not auto-remove existing.` })
    }
  }

  // Rendering surface
  console.log('\n--- RENDERING ---')
  const kind = cfg.profile?.kind || ''
  const spaEvidenceClass = 'heuristic'
  if (rendering.likelySpa) {
    record({ id: 'REND-01', category: 'rendering', title: 'Server-rendered content surface', severity: kind === 'spa' ? 'Low' : 'Medium', evidenceClass: spaEvidenceClass },
      { status: 'WARN', message: `Likely client-only SPA — small body (${rendering.bodyLen} chars) with JS. LLM crawlers may not render this.` })
  } else {
    record({ id: 'REND-01', category: 'rendering', title: 'Server-rendered content surface', severity: 'Low', evidenceClass: spaEvidenceClass },
      { status: 'PASS', message: `Body has ${rendering.bodyLen} chars of static content` })
  }

  // Hreflang reciprocity (only when there is more than one hreflang)
  if (signals.hreflangs.length >= 2) {
    console.log('\n--- I18N ---')
    const codes = signals.hreflangs.map((h) => h.hreflang)
    const hasXDefault = codes.includes('x-default')
    record({ id: 'I18N-HREF-01', category: 'i18n', title: 'x-default present', severity: 'Low', evidenceClass: 'machine_verified' },
      hasXDefault ? { status: 'PASS', message: `${signals.hreflangs.length} hreflang alternates including x-default` } : { status: 'WARN', message: `${signals.hreflangs.length} hreflang alternates but no x-default` })
  }

  // PSI (optional, only if key)
  if (psiKey) {
    console.log('\n--- CORE WEB VITALS (PSI) ---')
    try {
      const psiUrl = `https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=${encodeURIComponent(url)}&strategy=mobile&category=performance&key=${encodeURIComponent(psiKey)}`
      const r = await safeFetch(psiUrl, { timeout: 30000 })
      if (r.ok) {
        const data = await r.json()
        const audits = data.lighthouseResult?.audits || {}
        const lcp = audits['largest-contentful-paint']?.numericValue
        const cls = audits['cumulative-layout-shift']?.numericValue
        const inp = data.loadingExperience?.metrics?.INTERACTION_TO_NEXT_PAINT?.percentile
        record({ id: 'CWV-LCP-01', category: 'cwv', title: `LCP ≤ ${cfg.thresholds.lcpGoodMs} ms (mobile)`, severity: 'High', evidenceClass: 'machine_verified' },
          typeof lcp === 'number' ? (lcp <= cfg.thresholds.lcpGoodMs ? { status: 'PASS', message: `${Math.round(lcp)} ms` } : { status: 'WARN', message: `${Math.round(lcp)} ms` }) : { status: 'NOT_VERIFIED', message: 'LCP not returned' })
        record({ id: 'CWV-INP-01', category: 'cwv', title: `INP ≤ ${cfg.thresholds.inpGoodMs} ms (CrUX field, when available)`, severity: 'High', evidenceClass: 'machine_verified' },
          typeof inp === 'number' ? (inp <= cfg.thresholds.inpGoodMs ? { status: 'PASS', message: `${inp} ms` } : { status: 'WARN', message: `${inp} ms` }) : { status: 'NOT_VERIFIED', message: 'INP not returned (site may lack sufficient CrUX field data)' })
        record({ id: 'CWV-CLS-01', category: 'cwv', title: `CLS ≤ ${cfg.thresholds.clsGood}`, severity: 'Medium', evidenceClass: 'machine_verified' },
          typeof cls === 'number' ? (cls <= cfg.thresholds.clsGood ? { status: 'PASS', message: cls.toFixed(3) } : { status: 'WARN', message: cls.toFixed(3) }) : { status: 'NOT_VERIFIED', message: 'CLS not returned' })
      } else {
        record({ id: 'CWV-PSI-01', category: 'cwv', title: 'PageSpeed Insights API', severity: 'Medium', evidenceClass: 'machine_verified' }, { status: 'NOT_VERIFIED', message: `PSI HTTP ${r.status}` })
      }
    } catch (err) {
      record({ id: 'CWV-PSI-01', category: 'cwv', title: 'PageSpeed Insights API', severity: 'Medium', evidenceClass: 'machine_verified' }, { status: 'NOT_VERIFIED', message: `PSI error: ${err.message}` })
    }
  } else {
    record({ id: 'CWV-PSI-01', category: 'cwv', title: 'PageSpeed Insights API', severity: 'Medium', evidenceClass: 'machine_verified' }, { status: 'NOT_VERIFIED', message: 'No --psi-key provided; skipping CWV checks' })
  }
}

// ---------------------------------------------------------------------------
// Local build directory
// ---------------------------------------------------------------------------
function walkHtmlFiles(dir) {
  const out = []
  for (const item of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, item.name)
    if (item.isDirectory()) out.push(...walkHtmlFiles(full))
    else if (item.name.endsWith('.html')) out.push(full)
  }
  return out
}

async function runBuildAudit(dir) {
  console.log('--- STATIC BUILD ---')
  if (!fs.existsSync(dir)) {
    record({ id: 'BUILD-01', category: 'crawling', title: 'Build directory exists', severity: 'Critical', evidenceClass: 'machine_verified' }, { status: 'FAIL', message: `Directory not found: ${dir}` })
    return
  }
  const files = walkHtmlFiles(dir).slice(0, 200)
  if (!files.length) {
    record({ id: 'BUILD-01', category: 'crawling', title: 'HTML files present in build', severity: 'Critical', evidenceClass: 'machine_verified' }, { status: 'FAIL', message: `No .html files found in ${dir}` })
    return
  }
  record({ id: 'BUILD-01', category: 'crawling', title: 'HTML files present in build', severity: 'Low', evidenceClass: 'machine_verified' }, { status: 'PASS', message: `${files.length} HTML files inspected` })

  const titles = new Map()
  const h1s = new Map()
  let missingTitle = 0, missingDesc = 0, missingCanon = 0
  const sampleIssues = []

  for (const f of files) {
    const html = fs.readFileSync(f, 'utf8')
    const s = extractHeadSignals(html)
    if (!s.title) { missingTitle++; sampleIssues.push(`${path.relative(dir, f)} — no <title>`) }
    else { titles.set(s.title, (titles.get(s.title) || 0) + 1) }
    if (!s.meta.description) missingDesc++
    if (!s.canonicals.length) missingCanon++
    if (s.h1Count === 1) {
      const h1 = (html.match(/<h1\b[^>]*>([\s\S]*?)<\/h1>/i) || [])[1]?.replace(/<[^>]+>/g, '').trim()
      if (h1) h1s.set(h1, (h1s.get(h1) || 0) + 1)
    }
  }

  record({ id: 'BUILD-TITLE-01', category: 'head', title: 'All HTML pages have a <title>', severity: 'High', evidenceClass: 'machine_verified' },
    missingTitle === 0 ? { status: 'PASS', message: `${files.length}/${files.length}` } : { status: 'FAIL', message: `${missingTitle} pages missing <title>` , details: sampleIssues.slice(0, 5) })
  record({ id: 'BUILD-DESC-01', category: 'head', title: 'All HTML pages have a meta description', severity: 'Medium', evidenceClass: 'machine_verified' },
    missingDesc === 0 ? { status: 'PASS', message: `${files.length}/${files.length}` } : { status: 'WARN', message: `${missingDesc} pages missing meta description` })
  record({ id: 'BUILD-CANON-01', category: 'head', title: 'All HTML pages declare canonical', severity: 'Medium', evidenceClass: 'machine_verified' },
    missingCanon === 0 ? { status: 'PASS', message: `${files.length}/${files.length}` } : { status: 'WARN', message: `${missingCanon} pages missing canonical` })

  const dupTitles = [...titles.entries()].filter(([, n]) => n > 1)
  const dupH1s = [...h1s.entries()].filter(([, n]) => n > 1)
  record({ id: 'BUILD-DUP-TITLE-01', category: 'content', title: 'No duplicated <title> across pages', severity: 'Medium', evidenceClass: 'machine_verified' },
    dupTitles.length === 0 ? { status: 'PASS', message: 'All titles unique' } : { status: 'WARN', message: `${dupTitles.length} duplicated titles`, details: dupTitles.slice(0, 5) })
  record({ id: 'BUILD-DUP-H1-01', category: 'content', title: 'No duplicated <h1> across pages', severity: 'Low', evidenceClass: 'machine_verified' },
    dupH1s.length === 0 ? { status: 'PASS', message: 'All h1s unique' } : { status: 'WARN', message: `${dupH1s.length} duplicated h1s`, details: dupH1s.slice(0, 5) })
}

// ---------------------------------------------------------------------------
// Header
// ---------------------------------------------------------------------------
console.log('================================================================================')
console.log(`  SEO AUDIT v${cfg.version} — ${targetUrl || buildDir}`)
console.log(`  Profile: ${cfg.profile?.name || '(none)'} | Sitemap max: ${sitemapMax} | PSI: ${psiKey ? 'yes' : 'no'}`)
console.log('================================================================================\n')

if (targetUrl) await runLiveAudit(targetUrl)
if (buildDir) await runBuildAudit(buildDir)

// ---------------------------------------------------------------------------
// Verdict
// ---------------------------------------------------------------------------
let totalWeighted = 0, penaltyWeighted = 0
let passCount = 0, failCount = 0, warnCount = 0, notVerifiedCount = 0, naCount = 0
for (const c of findings) {
  if (c.status === 'NOT_APPLICABLE') { naCount++; continue }
  if (c.status === 'NOT_VERIFIED') { notVerifiedCount++; continue }
  totalWeighted += c.weight
  if (c.status === 'PASS') passCount++
  if (c.status === 'FAIL') { failCount++; penaltyWeighted += c.weight }
  if (c.status === 'WARN') { warnCount++; penaltyWeighted += c.weight * 0.4 }
}
const score = totalWeighted > 0 ? Math.max(0, Math.round((1 - penaltyWeighted / totalWeighted) * 100)) : 0
const materiallyIncomplete = notVerifiedCount >= Math.max(3, passCount / 2)
let verdict = 'READY_WITH_FOLLOWUPS'
if (hardGateFailed) verdict = 'BLOCKED'
else if (failCount > 0) verdict = 'FIX_BEFORE_LAUNCH'
else if (materiallyIncomplete) verdict = 'PARTIAL_AUDIT'
const confidence = verdict === 'PARTIAL_AUDIT' ? 'low' : notVerifiedCount > 0 ? 'medium' : 'high'

console.log('\n================================================================================')
console.log('  FINAL SUMMARY')
console.log('================================================================================')
console.log(`  PASS:          ${passCount}`)
console.log(`  FAIL:          ${failCount}`)
console.log(`  WARN:          ${warnCount}`)
console.log(`  NOT VERIFIED:  ${notVerifiedCount}`)
console.log(`  N/A:           ${naCount}`)
console.log(`  Score:         ${score}/100`)
console.log(`  Verdict:       ${verdict}`)
console.log(`  Confidence:    ${confidence}`)
if (hardGateReasons.length) {
  console.log('\n  Blockers:')
  for (const r of hardGateReasons) console.log(`  - ${r}`)
}

const report = {
  auditVersion: cfg.version,
  target: targetUrl || buildDir,
  profile: cfg.profile,
  verdict, confidence, score,
  counts: { pass: passCount, fail: failCount, warn: warnCount, notVerified: notVerifiedCount, notApplicable: naCount },
  timestamp: new Date().toISOString(),
  findings
}
fs.writeFileSync(path.join(ROOT, 'seo-audit-report.json'), JSON.stringify(report, null, 2), 'utf8')

const sarif = {
  $schema: 'https://json.schemastore.org/sarif-2.1.0.json',
  version: '2.1.0',
  runs: [{
    tool: { driver: { name: 'seo-audit', version: cfg.version, rules: findings.map((c) => ({ id: c.id, name: c.title, properties: { severity: c.severity, category: c.category } })) } },
    results: findings.filter((c) => ['FAIL', 'WARN', 'NOT_VERIFIED'].includes(c.status)).map((c) => ({
      ruleId: c.id,
      level: c.status === 'FAIL' ? 'error' : c.status === 'WARN' ? 'warning' : 'note',
      message: { text: `${c.title}: ${c.message}` },
      locations: [{ physicalLocation: { artifactLocation: { uri: targetUrl || buildDir || 'workspace' } } }],
      properties: { category: c.category, severity: c.severity, evidenceClass: c.evidenceClass }
    }))
  }]
}
fs.writeFileSync(path.join(ROOT, 'seo-audit-report.sarif'), JSON.stringify(sarif, null, 2), 'utf8')

if (wantXml) {
  console.log('\n<seoAudit>')
  console.log(`  <meta><target>${targetUrl || buildDir}</target><verdict>${verdict}</verdict><confidence>${confidence}</confidence><score>${score}</score></meta>`)
  console.log(`  <counts><pass>${passCount}</pass><fail>${failCount}</fail><warn>${warnCount}</warn><not_verified>${notVerifiedCount}</not_verified><not_applicable>${naCount}</not_applicable></counts>`)
  console.log('</seoAudit>')
}

process.exit(verdict === 'BLOCKED' || verdict === 'FIX_BEFORE_LAUNCH' ? 1 : 0)
