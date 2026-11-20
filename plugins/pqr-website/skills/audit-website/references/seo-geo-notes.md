# GEO / AEO Notes (2026)

GEO is not a separate discipline: Google states that *"from Google Search's
perspective, optimizing for generative AI search is optimizing for the search
experience, and thus still SEO."* This skill frames GEO as SEO fundamentals
applied to AI-search surfaces — never as a new lever to sell.

## What is verifiable

- Server HTML contains meaningful answers **without JS execution** (many AI
  crawlers fetch raw HTML and do not render JS; Googlebot does).
- The `robots.txt` decision for each AI crawler is explicit — and each claim is
  made on the **right** bot (`references/seo-ai-crawlers.md`).
- `llms.txt` presence and shape (reported, not scored).
- Structured data parses.
- Field Core Web Vitals (CrUX) when a PSI key or the declared data command is
  available.

## What is not verifiable

- Whether a specific LLM will cite the page. No skill can promise this.
- Ranking uplift in AI Overviews / AI Mode. These rest on the classic ranking
  systems; good SEO still matters, but no skill can prove an outcome.
- The effect of `llms.txt`: Google publicly states it is **not needed** and does
  not help or hurt visibility or rankings. Some non-Google systems may read it.
  Reported as `WARN` at most, never as a citation lever.
- The effect of any schema type on LLM citation. Do not claim one.

## AI search is not one surface

AI Overviews and AI Mode reach the same conclusion ~86% of the time but cite the
same URLs only ~13.7% of the time (third-party). Ranking well feeds AI Overviews;
AI Mode draws from a broader pool where freshness and entity authority weigh more
than raw position. Score both, and cite any third-party figure with its source
and date or leave it out.

## Crawler access

The full taxonomy — training vs search citability, per-bot, with the
claim-to-bot matrix — lives in `references/seo-ai-crawlers.md`. Read it before
reporting any "AI crawler" finding; the wrong-bot claim is a false finding.

## What the skill produces

- `PASS/WARN/FAIL/NOT_VERIFIED` on the verifiable items above.
- Honest wording in messages. No promises of citation.
- Findings flagged `heuristic` where the evidence is a pattern, not a probe —
  and a heuristic **never** raises a critical `FAIL`.
