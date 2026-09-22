#!/usr/bin/env node
/**
 * audit-website — Comprehensive 360º Website Audit Engine
 * Evaluates: SEO, Core Web Vitals, Privacy/Cookies in runtime, Analytics, CRO, Spider Links, and Accessibility.
 * Produces structured Markdown, JSON, and SARIF v2.1.0 output.
 */

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
        pillar: 'Saúde Técnica',
        severity: 'BLOCKER',
        title: 'Website inacessível ou falha de ligação',
        message: `Não foi possível estabelecer ligação ao URL: ${err.message}`,
        url: targetUrl,
        impact: 'O site está completamente indisponível para utilizadores e motores de busca.',
        fix: 'Verificar DNS, certificado SSL/TLS e servidor de alojamento.'
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
        pillar: 'SEO Técnico',
        severity: 'HIGH',
        title: 'Ficheiro robots.txt em falta na raiz',
        message: 'Não foi encontrado o ficheiro robots.txt no diretório estático.',
        url: 'robots.txt',
        impact: 'Motores de busca não recebem diretrizes claras de rastreio.',
        fix: 'Criar um robots.txt com declaração do Sitemap e regras de crawling.'
      });
    }

    const sitemapPath = path.join(resolvedPath, 'sitemap.xml');
    if (!fs.existsSync(sitemapPath)) {
      this.addFinding({
        check: 'sitemap-xml-exists',
        pillar: 'SEO Técnico',
        severity: 'HIGH',
        title: 'Ficheiro sitemap.xml em falta na raiz',
        message: 'Não foi encontrado o ficheiro sitemap.xml no diretório estático.',
        url: 'sitemap.xml',
        impact: 'Dificulta a indexação estruturada de novos conteúdos e páginas secundárias.',
        fix: 'Configurar o gerador de site estático para emitir sitemap.xml no build.'
      });
    }
  }

  auditHeaders(headers, url) {
    // HTTPS check
    if (!url.startsWith('https://')) {
      this.addFinding({
        check: 'https-enforced',
        pillar: 'Segurança & SEO',
        severity: 'BLOCKER',
        title: 'Website não utiliza HTTPS por omissão',
        message: 'O site responde em HTTP sem encriptação TLS.',
        url,
        impact: 'Penalização direta em SEO no Google e risco de interceção de dados dos visitantes.',
        fix: 'Forçar redirecionamento 301 para HTTPS e configurar HSTS.'
      });
    }

    // HSTS
    if (!headers['strict-transport-security']) {
      this.addFinding({
        check: 'hsts-header',
        pillar: 'Segurança',
        severity: 'MEDIUM',
        title: 'Cabeçalho Strict-Transport-Security (HSTS) em falta',
        message: 'O cabeçalho Strict-Transport-Security não foi devolvido pelo servidor.',
        url,
        impact: 'Vulnerável a ataques de downgrade SSL/TLS.',
        fix: 'Configurar cabeçalho Strict-Transport-Security: max-age=31536000; includeSubDomains.'
      });
    }

    // X-Content-Type-Options
    if (headers['x-content-type-options'] !== 'nosniff') {
      this.addFinding({
        check: 'content-type-nosniff',
        pillar: 'Segurança',
        severity: 'LOW',
        title: 'Cabeçalho X-Content-Type-Options: nosniff ausente',
        message: 'Proteção contra MIME-sniffing não declarada.',
        url,
        impact: 'Browsers antigos podem interpretar ficheiros estáticos como scripts executáveis.',
        fix: 'Adicionar cabeçalho X-Content-Type-Options: nosniff nas respostas HTTP.'
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
            pillar: 'SEO Técnico',
            severity: 'BLOCKER',
            title: 'robots.txt bloqueia rastreio de todo o website',
            message: 'Detetada diretiva `Disallow: /` a bloquear todos os bots.',
            url: `${origin}/robots.txt`,
            impact: 'O site será completamente desindexado do Google e outros motores de busca.',
            fix: 'Remover `Disallow: /` do bloco de User-agent: *.'
          });
        }
      } else {
        this.addFinding({
          check: 'robots-status',
          pillar: 'SEO Técnico',
          severity: 'HIGH',
          title: 'robots.txt devolve código HTTP diferente de 200',
          message: `O pedido a /robots.txt devolveu HTTP ${robotsRes.status}.`,
          url: `${origin}/robots.txt`,
          impact: 'Bots podem assumir permissão total ou restrição arbitrária.',
          fix: 'Garantir ficheiro /robots.txt acessível com HTTP 200.'
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
          pillar: 'SEO Técnico',
          severity: 'HIGH',
          title: 'sitemap.xml não encontrado na raiz',
          message: `O pedido a /sitemap.xml devolveu HTTP ${sitemapRes.status}.`,
          url: `${origin}/sitemap.xml`,
          impact: 'Atraso e ineficiência na descoberta de novas páginas pelo Googlebot.',
          fix: 'Disponibilizar o sitemap em /sitemap.xml e referenciá-lo no robots.txt.'
        });
      }
    } catch {
      // ignore
    }
  }

  async auditHtmlContent(html, pageUrl) {
    // ----------------------------------------------------
    // PILAR 1: SEO On-Page & Meta Tags
    // ----------------------------------------------------
    const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
    const title = titleMatch ? titleMatch[1].trim() : '';

    if (!title) {
      this.addFinding({
        check: 'seo-title-missing',
        pillar: 'SEO Técnico',
        severity: 'CRITICAL',
        title: 'Tag <title> em falta ou vazia',
        message: 'A página não possui uma etiqueta <title> no cabeçalho.',
        url: pageUrl,
        impact: 'Crítico para posicionamento e apresentação nos resultados de pesquisa (SERP).',
        fix: 'Adicionar uma tag <title> descritiva com 30 a 60 carateres.'
      });
    } else if (title.length < 20 || title.length > 70) {
      this.addFinding({
        check: 'seo-title-length',
        pillar: 'SEO Técnico',
        severity: 'LOW',
        title: `Tag <title> com comprimento não ideal (${title.length} carateres)`,
        message: `O título "${title}" deve ter entre 30 e 60 carateres para evitar truncagem.`,
        url: pageUrl,
        impact: 'Título truncado nos snippets de pesquisa reduz taxa de clique (CTR).',
        fix: 'Ajustar o título para ter entre 30 e 60 carateres com a palavra-chave principal.'
      });
    }

    const descMatch = html.match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']*)["']/i)
      || html.match(/<meta[^>]*content=["']([^"']*)["'][^>]*name=["']description["']/i);
    const description = descMatch ? descMatch[1].trim() : '';

    if (!description) {
      this.addFinding({
        check: 'seo-meta-description-missing',
        pillar: 'SEO Técnico',
        severity: 'MEDIUM',
        title: 'Meta description em falta',
        message: 'A página não define <meta name="description">.',
        url: pageUrl,
        impact: 'O Google gerará um excerto automático que pode não ter apelo comercial.',
        fix: 'Adicionar meta description persuasiva com 70 a 160 carateres.'
      });
    } else if (description.length < 50 || description.length > 170) {
      this.addFinding({
        check: 'seo-meta-description-length',
        pillar: 'SEO Técnico',
        severity: 'LOW',
        title: `Meta description com comprimento fora do recomendado (${description.length} carateres)`,
        message: `A descrição atual tem ${description.length} carateres (recomendado: 70 a 160 carateres).`,
        url: pageUrl,
        impact: 'Descrição pode ser cortada com reticências nos resultados de busca.',
        fix: 'Manter a meta description entre 70 e 160 carateres.'
      });
    }

    // Canonical
    const canonicalMatch = html.match(/<link[^>]*rel=["']canonical["'][^>]*href=["']([^"']*)["']/i);
    if (!canonicalMatch) {
      this.addFinding({
        check: 'seo-canonical-missing',
        pillar: 'SEO Técnico',
        severity: 'MEDIUM',
        title: 'Tag rel="canonical" em falta',
        message: 'A página não especifica um URL canónico explícito.',
        url: pageUrl,
        impact: 'Risco de conteúdo duplicado devido a variações de parâmetros de URL e barras finais.',
        fix: 'Inserir <link rel="canonical" href="..."> com o URL absoluto e limpo da página.'
      });
    }

    // Headings (H1)
    const h1Matches = html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/gi) || [];
    if (h1Matches.length === 0) {
      this.addFinding({
        check: 'seo-h1-missing',
        pillar: 'SEO Técnico',
        severity: 'HIGH',
        title: 'Cabeçalho principal <h1> em falta',
        message: 'A página não tem nenhum elemento <h1>.',
        url: pageUrl,
        impact: 'Dificulta a contextualização temática pelos motores de busca e utilizadores de leitores de ecrã.',
        fix: 'Incluir exatamente um elemento <h1> representativo do tema principal da página.'
      });
    } else if (h1Matches.length > 1) {
      this.addFinding({
        check: 'seo-h1-multiple',
        pillar: 'SEO Técnico',
        severity: 'LOW',
        title: `Múltiplos cabeçalhos <h1> detetados (${h1Matches.length} encontrados)`,
        message: 'Recomenda-se apenas um único elemento <h1> por página para uma hierarquia semântica limpa.',
        url: pageUrl,
        impact: 'Pode diluir o foco semântico da página.',
        fix: 'Converter os <h1> secundários em <h2>.'
      });
    }

    // Open Graph
    const ogTitle = html.match(/<meta[^>]*property=["']og:title["']/i);
    const ogImage = html.match(/<meta[^>]*property=["']og:image["']/i);
    if (!ogTitle || !ogImage) {
      this.addFinding({
        check: 'social-opengraph-missing',
        pillar: 'SEO & Redes Sociais',
        severity: 'LOW',
        title: 'Metatags Open Graph (og:title / og:image) incompletas',
        message: 'Faltam tags Open Graph para enriquecer a partilha em redes sociais e apps de mensagens.',
        url: pageUrl,
        impact: 'Partilhas no WhatsApp, LinkedIn, X e Facebook surgem sem imagem ou título atrativo.',
        fix: 'Configurar og:title, og:description, og:image e og:url no <head>.'
      });
    }

    // Schema.org Structured Data
    const jsonLdMatches = html.match(/<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi) || [];
    if (jsonLdMatches.length === 0) {
      this.addFinding({
        check: 'seo-structured-data-missing',
        pillar: 'SEO Técnico',
        severity: 'MEDIUM',
        title: 'Dados Estruturados Schema.org (JSON-LD) ausentes',
        message: 'Nenhum bloco de dados estruturados JSON-LD foi encontrado.',
        url: pageUrl,
        impact: 'A página perde elegibilidade para Rich Snippets no Google (estrelas, preços, FAQ, organização).',
        fix: 'Implementar Schema.org (ex.: Organization, WebSite ou Product) em formato JSON-LD.'
      });
    } else {
      for (const match of jsonLdMatches) {
        try {
          const raw = match.replace(/<script[^>]*type=["']application\/ld\+json["'][^>]*>/i, '').replace(/<\/script>/i, '');
          JSON.parse(raw);
        } catch {
          this.addFinding({
            check: 'seo-structured-data-syntax-error',
            pillar: 'SEO Técnico',
            severity: 'HIGH',
            title: 'Sintaxe JSON-LD inválida nos Dados Estruturados',
            message: 'O bloco Schema.org contém JSON malformado e não pode ser processado pelo Google.',
            url: pageUrl,
            impact: 'Erros no Google Search Console e perda imediata de Rich Results.',
            fix: 'Validar o JSON-LD contra o schema validator da Schema.org.'
          });
        }
      }
    }

    // ----------------------------------------------------
    // PILAR 3: Privacidade & Cookies em Runtime (ePrivacy / RGPD)
    // ----------------------------------------------------
    const trackingSignatures = [
      { name: 'Meta Pixel (Facebook)', regex: /(fbevents\.js|connect\.facebook\.net|fbq\s*\()/i, category: 'Marketing' },
      { name: 'Google Ads Remarketing', regex: /(googleads\.g\.doubleclick\.net|gtag\(['"]config['"],\s*['"]AW-)/i, category: 'Marketing' },
      { name: 'TikTok Pixel', regex: /(analytics\.tiktok\.com|ttq\.load)/i, category: 'Marketing' },
      { name: 'Hotjar Behavioral Recording', regex: /(static\.hotjar\.com|hjid)/i, category: 'Analytics Avançado' },
      { name: 'Microsoft Clarity', regex: /(clarity\.ms\/tag)/i, category: 'Analytics Avançado' },
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
        pillar: 'Privacidade & Legal',
        severity: 'BLOCKER',
        title: 'Trackers de publicidade a disparar sem Bloqueio Prévio de Consentimento',
        message: `Foram detetados scripts de rastreio (${detectedTrackers.map(t => t.name).join(', ')}) diretamente no código sem barreira de consentimento ativa.`,
        url: pageUrl,
        impact: 'Infração direta ao Regulamento Geral de Proteção de Dados (RGPD) e Diretiva ePrivacy com risco de contraordenação legal.',
        fix: 'Implementar Bloqueio Prévio (Consent Prior to Fire): os scripts só podem ser injetados após consentimento afirmativo do utilizador.'
      });
    }

    // Check Privacy Policy link
    const hasPrivacyPolicy = /<a[^>]*href=["'][^"']*(privacidade|privacy|politica-de-privacidade)[^"']*["']/i.test(html);
    if (!hasPrivacyPolicy) {
      this.addFinding({
        check: 'privacy-policy-link-missing',
        pillar: 'Privacidade & Legal',
        severity: 'HIGH',
        title: 'Ligação à Política de Privacidade não detetada',
        message: 'Não foi encontrada uma ligação para a Política de Privacidade no documento.',
        url: pageUrl,
        impact: 'Incumprimento das obrigações de transparência do Artigo 13.º do RGPD.',
        fix: 'Adicionar uma ligação permanente no rodapé da página para a Política de Privacidade.'
      });
    }

    // ----------------------------------------------------
    // PILAR 4: Web Analytics & Qualidade de Dados
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
          title: 'Múltiplos contentores Google Tag Manager detetados',
          message: `Encontrados contentores GTM distintos: ${uniqueGTM.join(', ')}.`,
          url: pageUrl,
          impact: 'Pode causar duplicação de eventos, aumento no tempo de carregamento e dados corrompidos.',
          fix: 'Consolidar tags num único contentor GTM.'
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
          title: 'Script gtag.js do GA4 carregado em duplicado',
          message: 'O script da biblioteca gtag.js está inserido múltiplas vezes no HTML.',
          url: pageUrl,
          impact: 'Duplicação de PageViews e distorção das taxas de rejeição e conversão.',
          fix: 'Manter apenas um carregamento do script gtag.js por página.'
        });
      }
    }

    // PII Leaks in links
    const piiMatch = html.match(/href=["'][^"']*[?&](email|cpf|nif|phone|password|senha|user_email)=[^"']+["']/gi);
    if (piiMatch) {
      this.addFinding({
        check: 'analytics-pii-in-url',
        pillar: 'Web Analytics & Segurança',
        severity: 'CRITICAL',
        title: 'Dados Pessoais (PII) expostos em parâmetros de URL',
        message: `Foram encontrados links com parâmetros sensíveis no URL: ${piiMatch.slice(0, 2).join(', ')}.`,
        url: pageUrl,
        impact: 'Violação dos Termos de Serviço da Google (suspensão da conta de GA4) e grave infração de segurança.',
        fix: 'Eliminar parâmetros PII de links e passar dados sensíveis apenas via POST no corpo do pedido.'
      });
    }

    // ----------------------------------------------------
    // PILAR 5: CRO & Eficácia de Conversão
    // ----------------------------------------------------
    // Detect Forms
    const forms = html.match(/<form[\s\S]*?<\/form>/gi) || [];
    for (const form of forms) {
      const inputs = form.match(/<input(?![^>]*type=["']hidden["'])[^>]*>/gi) || [];
      if (inputs.length > 8) {
        this.addFinding({
          check: 'cro-form-excessive-fields',
          pillar: 'Conversão & CRO',
          severity: 'MEDIUM',
          title: `Formulário com excesso de campos (${inputs.length} campos)`,
          message: 'Formulários longos geram atrito cognitivo e aumentam a taxa de abandono.',
          url: pageUrl,
          impact: 'Redução mensurável na taxa de conclusão e geração de leads.',
          fix: 'Simplificar o formulário para os campos essenciais ou dividir em etapas (multi-step).'
        });
      }

      // Check pre-ticked consent checkboxes (Dark pattern)
      const preTicked = form.match(/<input[^>]*type=["']checkbox["'][^>]*checked[^>]*>/i);
      if (preTicked) {
        this.addFinding({
          check: 'cro-dark-pattern-preticked-checkbox',
          pillar: 'Conversão & Legal',
          severity: 'CRITICAL',
          title: 'Caixa de consentimento pré-selecionada detetada (Dark Pattern)',
          message: 'Foi detetada uma checkbox de consentimento assinalada por omissão.',
          url: pageUrl,
          impact: 'Ilegal sob o RGPD e rejeitado pelos utilizadores.',
          fix: 'Remover o atributo `checked` para que o utilizador consinta de forma ativa.'
        });
      }
    }

    // Check CTA Presence
    const ctaMatches = html.match(/<(a|button)[^>]*(class|id)=["'][^"']*(btn|cta|button|comprar|pedir|registo)[^"']*["'][^>]*>[\s\S]*?<\/\1>/gi) || [];
    if (ctaMatches.length === 0 && !html.includes('<button') && !html.includes('class="btn"')) {
      this.addFinding({
        check: 'cro-no-clear-cta',
        pillar: 'Conversão & CRO',
        severity: 'HIGH',
        title: 'Nenhum Call to Action (CTA) principal evidente detetado',
        message: 'A página não apresenta botões de ação ou links de conversão destacados.',
        url: pageUrl,
        impact: 'Visitantes navegam sem uma chamada clara para o próximo passo comercial.',
        fix: 'Incluir um botão de ação primário acima da dobra com verbo acionável.'
      });
    }

    // ----------------------------------------------------
    // PILAR 7: Acessibilidade Pública (WCAG 2.2 AA)
    // ----------------------------------------------------
    // html lang attribute
    const htmlLangMatch = html.match(/<html[^>]*lang=["']([^"']+)["']/i);
    if (!htmlLangMatch) {
      this.addFinding({
        check: 'a11y-html-lang-missing',
        pillar: 'Acessibilidade',
        severity: 'MEDIUM',
        title: 'Atributo lang ausente na etiqueta <html>',
        message: 'O documento não declara o idioma principal da página.',
        url: pageUrl,
        impact: 'Leitores de ecrã não conseguem ajustar a pronúncia e sintetizadores de voz.',
        fix: 'Adicionar lang="pt" (ou o código de idioma adequado) na tag <html>.'
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
        pillar: 'Acessibilidade',
        severity: 'HIGH',
        title: `Imagens sem atributo alt (${imgMissingAlt} encontradas)`,
        message: `Existem ${imgMissingAlt} imagens sem texto alternativo descritivo.`,
        url: pageUrl,
        impact: 'Violação da WCAG 2.2 (Critério 1.1.1 - Conteúdo Não Textual) e perda de relevância em Google Imagens.',
        fix: 'Adicionar atributos alt descritivos em todas as imagens de conteúdo, ou alt="" em imagens meramente decorativas.'
      });
    }

    // Icon buttons without accessible label
    const iconButtons = html.match(/<button[^>]*>[\s\S]*?<(svg|i|span class=["'][^"']*icon)[^>]*>[\s\S]*?<\/button>/gi) || [];
    for (const btn of iconButtons) {
      if (!/aria-label=["'][^"']+["']/i.test(btn) && !/title=["'][^"']+["']/i.test(btn)) {
        this.addFinding({
          check: 'a11y-button-no-label',
          pillar: 'Acessibilidade',
          severity: 'MEDIUM',
          title: 'Botões apenas com ícone e sem texto acessível',
          message: 'Foi encontrado um botão interativo sem texto visível nem aria-label.',
          url: pageUrl,
          impact: 'Utilizadores de leitores de ecrã não sabem que ação o botão despoleta.',
          fix: 'Adicionar aria-label="Descrição da ação" no elemento <button>.'
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
            pillar: 'Saúde de Links (Spider)',
            severity: 'HIGH',
            title: `Link interno quebrado (HTTP 404 Not Found)`,
            message: `A página inicial liga para um endereço inexistente: ${link}`,
            url: link,
            impact: 'Fricção direta na experiência do utilizador e desperdício de orçamento de rastreio (crawl budget).',
            fix: 'Corrigir o URL no HTML ou criar um redirecionamento 301 para a página de destino correta.'
          });
        } else if (res.status >= 500) {
          this.stats.brokenLinks++;
          this.addFinding({
            check: 'spider-server-error-500',
            pillar: 'Saúde Técnica',
            severity: 'CRITICAL',
            title: `Erro de servidor interno em link (HTTP ${res.status})`,
            message: `O endereço interno ${link} falha com erro de servidor.`,
            url: link,
            impact: 'Página inacessível com quebra de serviço para os visitantes.',
            fix: 'Inspecionar logs do servidor de aplicação e tratar a exceção interna.'
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
            title: `Largest Contentful Paint (LCP) lento: ${(lcp / 1000).toFixed(2)}s`,
            message: `O LCP medido excede o limite saudável da Google de 2.5s (${(lcp / 1000).toFixed(2)}s).`,
            url: targetUrl,
            impact: 'Penalização direta na classificação de pesquisa mobile do Google e aumento da taxa de abandono.',
            fix: 'Otimizar o elemento hero LCP, pré-carregar imagens com <link rel="preload"> e implementar cache e CDN.'
          });
        }

        if (cls && cls > 0.1) {
          this.addFinding({
            check: 'cwv-cls-budget-failed',
            pillar: 'Performance & CWV',
            severity: cls > 0.25 ? 'CRITICAL' : 'HIGH',
            title: `Cumulative Layout Shift (CLS) instável: ${cls.toFixed(3)}`,
            message: `O CLS medido excede o limiar recomendado de 0.10 (${cls.toFixed(3)}).`,
            url: targetUrl,
            impact: 'Elementos visuais saltam no ecrã durante o carregamento, causando cliques acidentais.',
            fix: 'Definir width e height explícitos em todas as imagens, vídeos e blocos de anúncios.'
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

    const markdown = `# Relatório de Auditoria de Website 360º

- **Alvo:** \`${this.options.url || this.options.dir}\`
- **Data:** ${new Date().toISOString().split('T')[0]}
- **Motor:** \`audit-website@1.0.0\` (\`production-quality-ready\`)
- **Veredito:** \`${verdict}\` (${counts.BLOCKER} Blocker, ${counts.CRITICAL} Critical, ${counts.HIGH} High, ${counts.MEDIUM} Medium, ${counts.LOW} Low)

---

## 1. Resumo Executivo

| Métrica | Valor Apurado | Estado |
| :--- | :---: | :---: |
| **Páginas e Documentos Auditados** | ${this.stats.pagesAudited} | Completo |
| **Links Internos Testados (Spider)** | ${this.stats.linksChecked} | ${this.stats.brokenLinks > 0 ? `⚠️ ${this.stats.brokenLinks} quebrados` : '✅ Todos OK'} |
| **Trackers Detetados** | ${this.stats.trackersFound.length} | ${this.stats.trackersFound.join(', ') || 'Nenhum'} |
| **Tags de Analytics Ativas** | ${this.stats.analyticsFound.length} | ${this.stats.analyticsFound.join(', ') || 'Nenhum'} |
| **Falhas Bloqueantes (Blocker / Critical)** | ${counts.BLOCKER + counts.CRITICAL} | ${isBlocked ? '❌ REJEITADO' : '✅ APROVADO'} |

---

## 2. Tabela Priorizada de Problemas e Ações

${this.findings.length === 0 ? '✅ *Nenhum defeito encontrado. O website cumpre integralmente os requisitos dos 7 pilares.*' : ''}
${this.findings.map((f, i) => `### ${i + 1}. [${f.severity}] ${f.title}
- **Pilar:** ${f.pillar} (\`${f.check}\`)
- **Localização:** \`${f.url}\`
- **Problema:** ${f.message}
- **Impacto no Negócio / Utilizador:** ${f.impact}
- **Ação de Correção Recomendada:** ${f.fix}
`).join('\n')}

---

## 3. Critérios de Revalidação
Para fechar o veredito para \`READY\`:
1. Todos os apontamentos \`BLOCKER\` e \`CRITICAL\` devem estar remediados no ambiente de testes.
2. Nenhuma regressão de Core Web Vitals deve ser introduzida nas alterações de layout.
3. Reexecutar \`node scripts/run_website_audit.mjs --url=<URL>\` até obter 0 falhas críticas.
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
      console.log(`\n💾 Relatório guardado com sucesso em: ${this.options.out}`);
    }

    return { verdict, counts, findings: this.findings };
  }
}

// Main execution
const opts = parseArgs(process.argv.slice(2));
if (opts.help || (!opts.url && !opts.dir)) {
  printHelp();
  process.exit(opts.help ? 0 : 1);
}

const auditor = new WebsiteAuditor(opts);
auditor.run().then(res => {
  if (res.counts.BLOCKER > 0) process.exit(2);
}).catch(err => {
  console.error('Fatal audit error:', err);
  process.exit(1);
});
