#!/usr/bin/env node
/**
 * audit-website — Comprehensive 360º Website Audit Engine
 * Evaluates: SEO, Core Web Vitals, Privacy/Cookies in runtime, Analytics, CRO, Spider Links, and Accessibility.
 * Produces structured Markdown, JSON, and SARIF v2.1.0 output.
 */

import { exitCleanly } from './exit.mjs'
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// Declared in external-resources.json (Tier 2). The only third-party host this script calls.
const PSI_ENDPOINT = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed';

// Helper for parsing CLI arguments
function parseArgs(args) {
  const options = {
    url: null,
    dir: null,
    psiKey: null,
    spiderMax: 25,
    json: false,
    sarif: false,
    out: null,
    help: false
  };

  for (const arg of args) {
    if (arg === '--help' || arg === '-h') options.help = true;
    else if (arg.startsWith('--url=')) options.url = arg.split('=')[1].trim();
    else if (arg.startsWith('--dir=')) options.dir = arg.split('=')[1].trim();
    else if (arg.startsWith('--psi-key=')) options.psiKey = arg.split('=')[1].trim();
    else if (arg.startsWith('--spider-max=')) options.spiderMax = parseInt(arg.split('=')[1].trim(), 10) || 25;
    else if (arg === '--json') options.json = true;
    else if (arg === '--sarif') options.sarif = true;
    else if (arg.startsWith('--out=')) options.out = arg.split('=')[1].trim();
  }

  return options;
}

function printHelp() {
  console.log(`
audit-website — 360º Website Audit Engine

Usage:
  node run_website_audit.mjs --url=<https-url> [options]
  node run_website_audit.mjs --dir=./dist [options]

Options:
  --url=URL           Live URL to audit (fetches HTML, robots.txt, sitemaps, headers)
  --dir=PATH          Local static build directory to audit (Astro, Next.js, dist/)
  --psi-key=KEY       Google PageSpeed Insights API key for CrUX field data
  --spider-max=N      Maximum internal links to crawl for 404 detection (default: 25)
  --json              Output raw JSON report to stdout
  --sarif             Output SARIF v2.1.0 format
  --out=FILE          Save Markdown report to designated file
  --help, -h          Show this help message
`);
}

class WebsiteAuditor {
  constructor(options) {
    this.options = options;
    this.findings = [];
    this.stats = {
      pagesAudited: 0,
      linksChecked: 0,
      brokenLinks: 0,
      trackersFound: [],
      analyticsFound: [],
      cwv: null
    };
  }

  addFinding({ check, pillar, severity, title, message, url, selector, impact, fix }) {
    this.findings.push({
      check,
      pillar,
      severity, // BLOCKER, CRITICAL, HIGH, MEDIUM, LOW, INFO
      title,
      message,
      url: url || this.options.url || 'local',
      selector: selector || null,
      impact,
      fix
    });
  }

  async run() {
    console.log(`\n🔍 Starting 360º Website Audit...`);
    if (this.options.url) {
      console.log(`🎯 Target URL: ${this.options.url}`);
      await this.auditLiveUrl(this.options.url);
    } else if (this.options.dir) {
      console.log(`📁 Target Directory: ${this.options.dir}`);
      await this.auditDirectory(this.options.dir);
    } else {
      console.error(`❌ Error: Either --url or --dir must be provided.`);
      printHelp();
      process.exit(1);
    }

    return this.generateReport();
  }

  async auditLiveUrl(targetUrl) {
    let html = '';
    let responseHeaders = {};
    let finalUrl = targetUrl;

    try {
      const res = await fetch(targetUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (compatible; WebsiteAuditor/1.0)'
        },
        redirect: 'follow'
      });
      finalUrl = res.url;
      res.headers.forEach((val, key) => { responseHeaders[key.toLowerCase()] = val; });
      html = await res.text();
      this.stats.pagesAudited++;
    } catch (err) {
      this.addFinding({
        check: 'site-reachable',
        pillar: 'Technical Health',
        severity: 'BLOCKER',
        title: 'Website unreachable or connection failed',
        message: `Could not connect to the URL: ${err.message}`,
        url: targetUrl,
        impact: 'The site is entirely unavailable to users and search engines.',
        fix: 'Check DNS, the SSL/TLS certificate and the hosting server.'
      });
      return;
    }

    // 1. Audit Headers & Security
    this.auditHeaders(responseHeaders, finalUrl);

    // 2. Audit robots.txt & sitemap.xml
    await this.auditRobotsAndSitemap(finalUrl);

    // 3. Audit Page HTML
    await this.auditHtmlContent(html, finalUrl);

    // 4. Spider Internal Links (Broken Links Detection)
    await this.spiderLinks(html, finalUrl);

    // 5. Audit Performance & Core Web Vitals (PSI)
    if (this.options.psiKey) {
      await this.auditPageSpeed(finalUrl);
    }
  }

  async auditDirectory(dirPath) {
    const resolvedPath = path.resolve(process.cwd(), dirPath);
    if (!fs.existsSync(resolvedPath)) {
      console.error(`❌ Error: Directory does not exist: ${resolvedPath}`);
      process.exit(1);
    }

    // Find html files
    const htmlFiles = [];
    const findHtml = (currentDir) => {
      const entries = fs.readdirSync(currentDir, { withFileTypes: true });
      for (const entry of entries) {
        const full = path.join(currentDir, entry.name);
        if (entry.isDirectory()) {
          if (!['node_modules', '.git'].includes(entry.name)) findHtml(full);
        } else if (entry.isFile() && entry.name.endsWith('.html')) {
          htmlFiles.push(full);
        }
      }
    };
    findHtml(resolvedPath);

    console.log(`📄 Found ${htmlFiles.length} HTML files to inspect.`);
    for (const file of htmlFiles.slice(0, 10)) { // sample up to 10 files
      const content = fs.readFileSync(file, 'utf-8');
      const relPath = path.relative(resolvedPath, file);
      await this.auditHtmlContent(content, relPath);
      this.stats.pagesAudited++;
    }

    // Check robots.txt and sitemap.xml in root
    const robotsPath = path.join(resolvedPath, 'robots.txt');
    if (!fs.existsSync(robotsPath)) {
      this.addFinding({
        check: 'robots-txt-exists',
        pillar: 'Technical SEO',
        severity: 'HIGH',
        title: 'robots.txt missing at the root',
        message: 'No robots.txt in the static directory.',
        url: 'robots.txt',
        impact: 'Search engines get no clear crawling directives.',
        fix: 'Create a robots.txt declaring the Sitemap and crawling rules.'
      });
    }

    const sitemapPath = path.join(resolvedPath, 'sitemap.xml');
    if (!fs.existsSync(sitemapPath)) {
      this.addFinding({
        check: 'sitemap-xml-exists',
        pillar: 'Technical SEO',
        severity: 'HIGH',
        title: 'sitemap.xml missing at the root',
        message: 'No sitemap.xml in the static directory.',
        url: 'sitemap.xml',
        impact: 'Hinders structured indexing of new content and secondary pages.',
        fix: 'Have the static site generator emit sitemap.xml at build.'
      });
    }
  }

  auditHeaders(headers, url) {
    // HTTPS check
    if (!url.startsWith('https://')) {
      this.addFinding({
        check: 'https-enforced',
        pillar: 'Security & SEO',
        severity: 'BLOCKER',
        title: 'Website does not use HTTPS by default',
        message: 'The site answers over HTTP without TLS.',
        url,
        impact: 'Direct Google SEO penalty and risk of intercepting visitor data.',
        fix: 'Force a 301 redirect to HTTPS and configure HSTS.'
      });
    }

    // HSTS
    if (!headers['strict-transport-security']) {
      this.addFinding({
        check: 'hsts-header',
        pillar: 'Security',
        severity: 'MEDIUM',
        title: 'Strict-Transport-Security (HSTS) header missing',
        message: 'The server did not return Strict-Transport-Security.',
        url,
        impact: 'Vulnerable to SSL/TLS downgrade attacks.',
        fix: 'Set Strict-Transport-Security: max-age=31536000; includeSubDomains.'
      });
    }

    // X-Content-Type-Options
    if (headers['x-content-type-options'] !== 'nosniff') {
      this.addFinding({
        check: 'content-type-nosniff',
        pillar: 'Security',
        severity: 'LOW',
        title: 'X-Content-Type-Options: nosniff header missing',
        message: 'No MIME-sniffing protection declared.',
        url,
        impact: 'Old browsers may run static files as scripts.',
        fix: 'Add X-Content-Type-Options: nosniff to HTTP responses.'
      });
    }
  }

  async auditRobotsAndSitemap(baseUrl) {
    const origin = new URL(baseUrl).origin;

    // robots.txt
    try {
      const robotsRes = await fetch(`${origin}/robots.txt`);
      if (robotsRes.status === 200) {
        const text = await robotsRes.text();
        if (text.includes('Disallow: /') && !text.includes('Disallow: /admin')) {
          this.addFinding({
            check: 'robots-disallow-all',
            pillar: 'Technical SEO',
            severity: 'BLOCKER',
            title: 'robots.txt blocks crawling of the whole site',
            message: 'A `Disallow: /` directive blocks every bot.',
            url: `${origin}/robots.txt`,
            impact: 'The site will be fully de-indexed from Google and other search engines.',
            fix: 'Remove `Disallow: /` from the User-agent: * block.'
          });
        }
      } else {
        this.addFinding({
          check: 'robots-status',
          pillar: 'Technical SEO',
          severity: 'HIGH',
          title: 'robots.txt returns an HTTP status other than 200',
          message: `/robots.txt returned HTTP ${robotsRes.status}.`,
          url: `${origin}/robots.txt`,
          impact: 'Bots may assume full permission or arbitrary restriction.',
          fix: 'Serve /robots.txt with HTTP 200.'
        });
      }
    } catch {
      // ignore network issue
    }

    // sitemap.xml
    try {
      const sitemapRes = await fetch(`${origin}/sitemap.xml`);
      if (sitemapRes.status !== 200) {
        this.addFinding({
          check: 'sitemap-status',
          pillar: 'Technical SEO',
          severity: 'HIGH',
          title: 'sitemap.xml not found at the root',
          message: `/sitemap.xml returned HTTP ${sitemapRes.status}.`,
          url: `${origin}/sitemap.xml`,
          impact: 'Slow, inefficient discovery of new pages by Googlebot.',
          fix: 'Serve the sitemap at /sitemap.xml and reference it in robots.txt.'
        });
      }
    } catch {
      // ignore
    }
  }

  async auditHtmlContent(html, pageUrl) {
    // ----------------------------------------------------
    // PILLAR 1: on-page SEO & meta tags
    // ----------------------------------------------------
    const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
    const title = titleMatch ? titleMatch[1].trim() : '';

    if (!title) {
      this.addFinding({
        check: 'seo-title-missing',
        pillar: 'Technical SEO',
        severity: 'CRITICAL',
        title: '<title> missing or empty',
        message: 'The page has no <title> in its head.',
        url: pageUrl,
        impact: 'Critical for ranking and presentation in search results (SERP).',
        fix: 'Add a descriptive <title> of 30 to 60 characters.'
      });
    } else if (title.length < 20 || title.length > 70) {
      this.addFinding({
        check: 'seo-title-length',
        pillar: 'Technical SEO',
        severity: 'LOW',
        title: `<title> length not ideal (${title.length} characters)`,
        message: `The title "${title}" should have 30 to 60 characters to avoid truncation.`,
        url: pageUrl,
        impact: 'A truncated title in search snippets lowers click-through (CTR).',
        fix: 'Make the title 30 to 60 characters, with the main keyword.'
      });
    }

    const descMatch = html.match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']*)["']/i)
      || html.match(/<meta[^>]*content=["']([^"']*)["'][^>]*name=["']description["']/i);
    const description = descMatch ? descMatch[1].trim() : '';

    if (!description) {
      this.addFinding({
        check: 'seo-meta-description-missing',
        pillar: 'Technical SEO',
        severity: 'MEDIUM',
        title: 'Meta description missing',
        message: 'The page defines no <meta name="description">.',
        url: pageUrl,
        impact: 'Google will generate an automatic snippet that may lack commercial appeal.',
        fix: 'Add a persuasive meta description of 70 to 160 characters.'
      });
    } else if (description.length < 50 || description.length > 170) {
      this.addFinding({
        check: 'seo-meta-description-length',
        pillar: 'Technical SEO',
        severity: 'LOW',
        title: `Meta description length outside the recommendation (${description.length} characters)`,
        message: `The current description has ${description.length} characters (recommended: 70 to 160).`,
        url: pageUrl,
        impact: 'The description may be cut with an ellipsis in search results.',
        fix: 'Keep the meta description between 70 and 160 characters.'
      });
    }

    // Canonical
    const canonicalMatch = html.match(/<link[^>]*rel=["']canonical["'][^>]*href=["']([^"']*)["']/i);
    if (!canonicalMatch) {
      this.addFinding({
        check: 'seo-canonical-missing',
        pillar: 'Technical SEO',
        severity: 'MEDIUM',
        title: 'rel="canonical" missing',
        message: 'The page declares no explicit canonical URL.',
        url: pageUrl,
        impact: 'Duplicate-content risk from URL parameter and trailing-slash variants.',
        fix: 'Add <link rel="canonical" href="..."> with the clean absolute URL of the page.'
      });
    }

    // Headings (H1)
    const h1Matches = html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/gi) || [];
    if (h1Matches.length === 0) {
      this.addFinding({
        check: 'seo-h1-missing',
        pillar: 'Technical SEO',
        severity: 'HIGH',
        title: 'Main <h1> heading missing',
        message: 'The page has no <h1> element.',
        url: pageUrl,
        impact: 'Hinders topical context for search engines and screen-reader users.',
        fix: 'Include exactly one <h1> stating the main topic of the page.'
      });
    } else if (h1Matches.length > 1) {
      this.addFinding({
        check: 'seo-h1-multiple',
        pillar: 'Technical SEO',
        severity: 'LOW',
        title: `Multiple <h1> headings (${h1Matches.length} found)`,
        message: 'One <h1> per page keeps the semantic hierarchy clean.',
        url: pageUrl,
        impact: 'May dilute the semantic focus of the page.',
        fix: 'Turn the secondary <h1>s into <h2>.'
      });
    }

    // Open Graph
    const ogTitle = html.match(/<meta[^>]*property=["']og:title["']/i);
    const ogImage = html.match(/<meta[^>]*property=["']og:image["']/i);
    if (!ogTitle || !ogImage) {
      this.addFinding({
        check: 'social-opengraph-missing',
        pillar: 'SEO & Social',
        severity: 'LOW',
        title: 'Incomplete Open Graph meta tags (og:title / og:image)',
        message: 'Open Graph tags are missing for rich sharing on social networks and messaging apps.',
        url: pageUrl,
        impact: 'Shares on WhatsApp, LinkedIn, X and Facebook show no image or attractive title.',
        fix: 'Set og:title, og:description, og:image and og:url in <head>.'
      });
    }

    // Schema.org Structured Data
    const jsonLdMatches = html.match(/<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi) || [];
    if (jsonLdMatches.length === 0) {
      this.addFinding({
        check: 'seo-structured-data-missing',
        pillar: 'Technical SEO',
        severity: 'MEDIUM',
        title: 'Schema.org structured data (JSON-LD) missing',
        message: 'No JSON-LD structured-data block found.',
        url: pageUrl,
        impact: 'The page loses Google rich-snippet eligibility (stars, prices, FAQ, organisation).',
        fix: 'Add Schema.org (Organization, WebSite or Product) as JSON-LD.'
      });
    } else {
      for (const match of jsonLdMatches) {
        try {
          const raw = match.replace(/<script[^>]*type=["']application\/ld\+json["'][^>]*>/i, '').replace(/<\/script>/i, '');
          JSON.parse(raw);
        } catch {
          this.addFinding({
            check: 'seo-structured-data-syntax-error',
            pillar: 'Technical SEO',
            severity: 'HIGH',
            title: 'Invalid JSON-LD syntax in the structured data',
            message: 'The Schema.org block holds malformed JSON Google cannot process.',
            url: pageUrl,
            impact: 'Google Search Console errors and immediate loss of rich results.',
            fix: 'Validate the JSON-LD with the Schema.org validator.'
          });
        }
      }
    }

    // ----------------------------------------------------
    // PILLAR 3: runtime privacy & cookies (ePrivacy / GDPR)
    // ----------------------------------------------------
    const trackingSignatures = [
      { name: 'Meta Pixel (Facebook)', regex: /(fbevents\.js|connect\.facebook\.net|fbq\s*\()/i, category: 'Marketing' },
      { name: 'Google Ads Remarketing', regex: /(googleads\.g\.doubleclick\.net|gtag\(['"]config['"],\s*['"]AW-)/i, category: 'Marketing' },
      { name: 'TikTok Pixel', regex: /(analytics\.tiktok\.com|ttq\.load)/i, category: 'Marketing' },
      { name: 'Hotjar Behavioral Recording', regex: /(static\.hotjar\.com|hjid)/i, category: 'Advanced Analytics' },
      { name: 'Microsoft Clarity', regex: /(clarity\.ms\/tag)/i, category: 'Advanced Analytics' },
      { name: 'Criteo Retargeting', regex: /(static\.criteo\.net)/i, category: 'Marketing' }
    ];

    const detectedTrackers = [];
    for (const tracker of trackingSignatures) {
      if (tracker.regex.test(html)) {
        detectedTrackers.push(tracker);
        if (!this.stats.trackersFound.includes(tracker.name)) {
          this.stats.trackersFound.push(tracker.name);
        }
      }
    }

    // Check if consent mode or consent wrapper is present
    const hasConsentBannerOrCMP = /(cookiebot|onetrust|didomi|klaro|axeptio|iubenda|cookie-consent|cookie-banner|cookie-notice)/i.test(html);
    const hasGoogleConsentMode = /gtag\s*\(\s*['"]consent['"]\s*,\s*['"]default['"]\s*,\s*\{[^}]*['"]ad_storage['"]\s*:\s*['"]denied['"]/i.test(html);

    if (detectedTrackers.length > 0 && !hasConsentBannerOrCMP && !hasGoogleConsentMode) {
      this.addFinding({
        check: 'privacy-cookie-consent-violation',
        pillar: 'Privacy & Legal',
        severity: 'BLOCKER',
        title: 'Advertising trackers firing without prior consent blocking',
        message: `Tracking scripts (${detectedTrackers.map(t => t.name).join(', ')}) are in the code with no active consent barrier.`,
        url: pageUrl,
        impact: 'Direct breach of the GDPR and the ePrivacy Directive, with risk of a fine.',
        fix: 'Implement consent prior to fire: inject the scripts only after affirmative consent from the user.'
      });
    }

    // Check Privacy Policy link
    const hasPrivacyPolicy = /<a[^>]*href=["'][^"']*(privacidade|privacy|politica-de-privacidade)[^"']*["']/i.test(html);
    if (!hasPrivacyPolicy) {
      this.addFinding({
        check: 'privacy-policy-link-missing',
        pillar: 'Privacy & Legal',
        severity: 'HIGH',
        title: 'No link to the privacy policy found',
        message: 'The document has no link to the privacy policy.',
        url: pageUrl,
        impact: 'Breach of the GDPR Article 13 transparency duties.',
        fix: 'Add a permanent footer link to the privacy policy.'
      });
    }

    // ----------------------------------------------------
    // PILLAR 4: web analytics & data quality
    // ----------------------------------------------------
    const gtmMatch = html.match(/GTM-[A-Z0-9]{4,10}/g);
    const ga4Match = html.match(/G-[A-Z0-9]{6,12}/g);

    if (gtmMatch) {
      const uniqueGTM = [...new Set(gtmMatch)];
      this.stats.analyticsFound.push(...uniqueGTM);
      if (uniqueGTM.length > 1) {
        this.addFinding({
          check: 'analytics-gtm-multiple',
          pillar: 'Web Analytics',
          severity: 'MEDIUM',
          title: 'Multiple Google Tag Manager containers found',
          message: `Distinct GTM containers: ${uniqueGTM.join(', ')}.`,
          url: pageUrl,
          impact: 'May duplicate events, slow loading and corrupt data.',
          fix: 'Consolidate tags in a single GTM container.'
        });
      }
    }

    if (ga4Match) {
      const uniqueGA4 = [...new Set(ga4Match)];
      this.stats.analyticsFound.push(...uniqueGA4);
      // Check for duplicate snippet calls
      const ga4Snippets = (html.match(/googletagmanager\.com\/gtag\/js\?id=G-/gi) || []).length;
      if (ga4Snippets > 1) {
        this.addFinding({
          check: 'analytics-ga4-duplicate-script',
          pillar: 'Web Analytics',
          severity: 'HIGH',
          title: 'GA4 gtag.js script loaded twice',
          message: 'The gtag.js library is inserted several times in the HTML.',
          url: pageUrl,
          impact: 'Duplicated page views and distorted bounce and conversion rates.',
          fix: 'Load gtag.js once per page.'
        });
      }
    }

    // PII Leaks in links
    const piiMatch = html.match(/href=["'][^"']*[?&](email|cpf|nif|phone|password|senha|user_email)=[^"']+["']/gi);
    if (piiMatch) {
      this.addFinding({
        check: 'analytics-pii-in-url',
        pillar: 'Web Analytics & Security',
        severity: 'CRITICAL',
        title: 'Personal data (PII) exposed in URL parameters',
        message: `Links carry sensitive URL parameters: ${piiMatch.slice(0, 2).join(', ')}.`,
        url: pageUrl,
        impact: 'Breach of the Google terms (GA4 account suspension) and a serious security fault.',
        fix: 'Remove PII parameters from links; send sensitive data only in a POST body.'
      });
    }

    // ----------------------------------------------------
    // PILLAR 5: CRO & conversion
    // ----------------------------------------------------
    // Detect Forms
    const forms = html.match(/<form[\s\S]*?<\/form>/gi) || [];
    for (const form of forms) {
      const inputs = form.match(/<input(?![^>]*type=["']hidden["'])[^>]*>/gi) || [];
      if (inputs.length > 8) {
        this.addFinding({
          check: 'cro-form-excessive-fields',
          pillar: 'Conversion & CRO',
          severity: 'MEDIUM',
          title: `Form with too many fields (${inputs.length})`,
          message: 'Long forms add cognitive friction and raise abandonment.',
          url: pageUrl,
          impact: 'Measurable drop in completion and lead generation.',
          fix: 'Keep only the essential fields, or split into steps (multi-step).'
        });
      }

      // Check pre-ticked consent checkboxes (Dark pattern)
      const preTicked = form.match(/<input[^>]*type=["']checkbox["'][^>]*checked[^>]*>/i);
      if (preTicked) {
        this.addFinding({
          check: 'cro-dark-pattern-preticked-checkbox',
          pillar: 'Conversion & Legal',
          severity: 'CRITICAL',
          title: 'Pre-ticked consent checkbox (dark pattern)',
          message: 'A consent checkbox is ticked by default.',
          url: pageUrl,
          impact: 'Illegal under the GDPR and rejected by users.',
          fix: 'Remove the `checked` attribute so the user consents actively.'
        });
      }
    }

    // Check CTA Presence
    const ctaMatches = html.match(/<(a|button)[^>]*(class|id)=["'][^"']*(btn|cta|button|comprar|pedir|registo)[^"']*["'][^>]*>[\s\S]*?<\/\1>/gi) || [];
    if (ctaMatches.length === 0 && !html.includes('<button') && !html.includes('class="btn"')) {
      this.addFinding({
        check: 'cro-no-clear-cta',
        pillar: 'Conversion & CRO',
        severity: 'HIGH',
        title: 'No evident primary call to action (CTA)',
        message: 'The page shows no prominent action buttons or conversion links.',
        url: pageUrl,
        impact: 'Visitors browse with no clear call to the next commercial step.',
        fix: 'Add a primary action button above the fold with an actionable verb.'
      });
    }

    // ----------------------------------------------------
    // PILLAR 7: public accessibility (WCAG 2.2 AA)
    // ----------------------------------------------------
    // html lang attribute
    const htmlLangMatch = html.match(/<html[^>]*lang=["']([^"']+)["']/i);
    if (!htmlLangMatch) {
      this.addFinding({
        check: 'a11y-html-lang-missing',
        pillar: 'Accessibility',
        severity: 'MEDIUM',
        title: 'lang attribute missing on <html>',
        message: 'The document does not declare the main language of the page.',
        url: pageUrl,
        impact: 'Screen readers cannot adjust pronunciation and speech synthesis.',
        fix: 'Add lang="en" (or the right language code) to <html>.'
      });
    }

    // Images without alt
    const imgMatches = html.match(/<img[^>]*>/gi) || [];
    let imgMissingAlt = 0;
    for (const img of imgMatches) {
      if (!/alt=["'][^"']*["']/i.test(img)) {
        imgMissingAlt++;
      }
    }
    if (imgMissingAlt > 0) {
      this.addFinding({
        check: 'a11y-img-alt-missing',
        pillar: 'Accessibility',
        severity: 'HIGH',
        title: `Images without alt (${imgMissingAlt} found)`,
        message: `${imgMissingAlt} images have no descriptive alternative text.`,
        url: pageUrl,
        impact: 'Fails WCAG 2.2 (SC 1.1.1 non-text content) and loses Google Images relevance.',
        fix: 'Add descriptive alt to every content image, or alt="" to purely decorative ones.'
      });
    }

    // Icon buttons without accessible label
    const iconButtons = html.match(/<button[^>]*>[\s\S]*?<(svg|i|span class=["'][^"']*icon)[^>]*>[\s\S]*?<\/button>/gi) || [];
    for (const btn of iconButtons) {
      if (!/aria-label=["'][^"']+["']/i.test(btn) && !/title=["'][^"']+["']/i.test(btn)) {
        this.addFinding({
          check: 'a11y-button-no-label',
          pillar: 'Accessibility',
          severity: 'MEDIUM',
          title: 'Icon-only buttons without accessible text',
          message: 'An interactive button has neither visible text nor aria-label.',
          url: pageUrl,
          impact: 'Screen-reader users cannot tell what the button does.',
          fix: 'Add aria-label="<action>" to the <button>.'
        });
        break; // emit once
      }
    }
  }

  async spiderLinks(html, baseUrl) {
    const origin = new URL(baseUrl).origin;
    const linkMatches = html.match(/<a[^>]*href=["']([^"']+)["']/gi) || [];
    const internalLinks = new Set();

    for (const match of linkMatches) {
      const hrefMatch = match.match(/href=["']([^"']+)["']/i);
      if (!hrefMatch) continue;
      const href = hrefMatch[1].trim();

      if (href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('javascript:')) {
        continue;
      }

      try {
        const resolved = new URL(href, baseUrl);
        if (resolved.origin === origin && resolved.pathname !== new URL(baseUrl).pathname) {
          internalLinks.add(resolved.href);
        }
      } catch {
        // invalid URL
      }
    }

    const sample = Array.from(internalLinks).slice(0, this.options.spiderMax);
    this.stats.linksChecked = sample.length;

    console.log(`🕷️  Spidering ${sample.length} internal links...`);
    for (const link of sample) {
      try {
        const res = await fetch(link, {
          method: 'HEAD',
          headers: { 'User-Agent': 'Mozilla/5.0 (compatible; WebsiteAuditor/1.0)' },
          redirect: 'follow'
        });

        if (res.status === 404) {
          this.stats.brokenLinks++;
          this.addFinding({
            check: 'spider-broken-link-404',
            pillar: 'Link Health (Spider)',
            severity: 'HIGH',
            title: `Broken internal link (HTTP 404 Not Found)`,
            message: `The home page links to a missing address: ${link}`,
            url: link,
            impact: 'Direct friction for users and wasted crawl budget.',
            fix: 'Fix the URL in the HTML or add a 301 redirect to the right page.'
          });
        } else if (res.status >= 500) {
          this.stats.brokenLinks++;
          this.addFinding({
            check: 'spider-server-error-500',
            pillar: 'Technical Health',
            severity: 'CRITICAL',
            title: `Internal server error on a link (HTTP ${res.status})`,
            message: `Internal address ${link} fails with a server error.`,
            url: link,
            impact: 'Page unreachable: service broken for visitors.',
            fix: 'Inspect the application server logs and handle the internal exception.'
          });
        }
      } catch {
        // network error on HEAD
      }
    }
  }

  async auditPageSpeed(targetUrl) {
    console.log(`⚡ Querying Google PageSpeed Insights API...`);
    try {
      const endpoint = new URL(PSI_ENDPOINT);
      endpoint.search = new URLSearchParams({ url: targetUrl, strategy: 'mobile', key: this.options.psiKey }).toString();
      const res = await fetch(endpoint);
      if (res.status === 200) {
        const data = await res.json();
        const experience = data.loadingExperience?.metrics;
        const lighthouse = data.lighthouseResult?.audits;

        const lcp = experience?.LARGEST_CONTENTFUL_PAINT_MS?.percentile || lighthouse?.['largest-contentful-paint']?.numericValue;
        const cls = experience?.CUMULATIVE_LAYOUT_SHIFT_SCORE?.percentile || lighthouse?.['cumulative-layout-shift']?.numericValue;

        this.stats.cwv = { lcp, cls };

        if (lcp && lcp > 2500) {
          this.addFinding({
            check: 'cwv-lcp-budget-failed',
            pillar: 'Performance & CWV',
            severity: lcp > 4000 ? 'CRITICAL' : 'HIGH',
            title: `Slow Largest Contentful Paint (LCP): ${(lcp / 1000).toFixed(2)}s`,
            message: `Measured LCP exceeds Google's healthy 2.5s limit (${(lcp / 1000).toFixed(2)}s).`,
            url: targetUrl,
            impact: 'Direct penalty in Google mobile ranking and higher abandonment.',
            fix: 'Optimise the LCP hero element, preload images with <link rel="preload">, add caching and a CDN.'
          });
        }

        if (cls && cls > 0.1) {
          this.addFinding({
            check: 'cwv-cls-budget-failed',
            pillar: 'Performance & CWV',
            severity: cls > 0.25 ? 'CRITICAL' : 'HIGH',
            title: `Unstable Cumulative Layout Shift (CLS): ${cls.toFixed(3)}`,
            message: `Measured CLS exceeds the recommended 0.10 (${cls.toFixed(3)}).`,
            url: targetUrl,
            impact: 'Elements jump while loading, causing accidental clicks.',
            fix: 'Set explicit width and height on every image, video and ad block.'
          });
        }
      }
    } catch (err) {
      console.warn(`⚠️ PageSpeed Insights API check failed: ${err.message}`);
    }
  }

  generateReport() {
    const counts = {
      BLOCKER: this.findings.filter(f => f.severity === 'BLOCKER').length,
      CRITICAL: this.findings.filter(f => f.severity === 'CRITICAL').length,
      HIGH: this.findings.filter(f => f.severity === 'HIGH').length,
      MEDIUM: this.findings.filter(f => f.severity === 'MEDIUM').length,
      LOW: this.findings.filter(f => f.severity === 'LOW').length,
      INFO: this.findings.filter(f => f.severity === 'INFO').length
    };

    const isBlocked = counts.BLOCKER > 0 || counts.CRITICAL > 0;
    const verdict = isBlocked ? 'BLOCKED' : (counts.HIGH > 0 ? 'FIX_BEFORE_LAUNCH' : 'READY');

    const markdown = `# 360º Website Audit Report

- **Target:** \`${this.options.url || this.options.dir}\`
- **Date:** ${new Date().toISOString().split('T')[0]}
- **Engine:** \`audit-website@1.0.0\` (\`production-quality-ready\`)
- **Verdict:** \`${verdict}\` (${counts.BLOCKER} Blocker, ${counts.CRITICAL} Critical, ${counts.HIGH} High, ${counts.MEDIUM} Medium, ${counts.LOW} Low)

---

## 1. Executive summary

| Metric | Value | State |
| :--- | :---: | :---: |
| **Pages and documents audited** | ${this.stats.pagesAudited} | Complete |
| **Internal links tested (spider)** | ${this.stats.linksChecked} | ${this.stats.brokenLinks > 0 ? `⚠️ ${this.stats.brokenLinks} broken` : '✅ All OK'} |
| **Trackers found** | ${this.stats.trackersFound.length} | ${this.stats.trackersFound.join(', ') || 'None'} |
| **Active analytics tags** | ${this.stats.analyticsFound.length} | ${this.stats.analyticsFound.join(', ') || 'None'} |
| **Blocking failures (Blocker / Critical)** | ${counts.BLOCKER + counts.CRITICAL} | ${isBlocked ? '❌ REJECTED' : '✅ APPROVED'} |

---

## 2. Prioritised problems and actions

${this.findings.length === 0 ? '✅ *No defect found. The website meets every requirement of the 7 pillars.*' : ''}
${this.findings.map((f, i) => `### ${i + 1}. [${f.severity}] ${f.title}
- **Pillar:** ${f.pillar} (\`${f.check}\`)
- **Location:** \`${f.url}\`
- **Problem:** ${f.message}
- **Business / user impact:** ${f.impact}
- **Recommended fix:** ${f.fix}
`).join('\n')}

---

## 3. Revalidation criteria
To close the verdict as \`READY\`:
1. Every \`BLOCKER\` and \`CRITICAL\` finding is fixed in the test environment.
2. No Core Web Vitals regression is introduced by layout changes.
3. Re-run \`node scripts/run_website_audit.mjs --url=<URL>\` until there are 0 critical failures.
`;

    if (this.options.json) {
      console.log(JSON.stringify({ verdict, counts, stats: this.stats, findings: this.findings }, null, 2));
    } else if (this.options.sarif) {
      const sarif = {
        $schema: 'https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json',
        version: '2.1.0',
        runs: [{
          tool: { driver: { name: 'audit-website', version: '1.0.0' } },
          results: this.findings.map(f => ({
            ruleId: f.check,
            level: f.severity === 'BLOCKER' || f.severity === 'CRITICAL' ? 'error' : (f.severity === 'HIGH' ? 'warning' : 'note'),
            message: { text: `${f.title}: ${f.message}` },
            locations: [{ physicalLocation: { artifactLocation: { uri: f.url } } }]
          }))
        }]
      };
      console.log(JSON.stringify(sarif, null, 2));
    } else {
      console.log(markdown);
    }

    if (this.options.out) {
      fs.writeFileSync(path.resolve(process.cwd(), this.options.out), markdown, 'utf-8');
      console.log(`\n💾 Report saved to: ${this.options.out}`);
    }

    return { verdict, counts, findings: this.findings };
  }
}

// Main execution
const opts = parseArgs(process.argv.slice(2));
if (opts.help || (!opts.url && !opts.dir)) {
  printHelp();
  exitCleanly(opts.help ? 0 : 1);
}

const auditor = new WebsiteAuditor(opts);
auditor.run().then(res => {
  if (res.counts.BLOCKER > 0) exitCleanly(2);
}).catch(err => {
  console.error('Fatal audit error:', err);
  process.exit(1);
});
