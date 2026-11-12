# GEO / AEO Notes (2026)

## What is verifiable
- Server HTML contains meaningful answers without JS execution (many LLM crawlers do not render JS).
- Robots policy for known LLM crawlers (`GPTBot`, `ClaudeBot`, `PerplexityBot`, `Google-Extended`) is explicit.
- `llms.txt` presence and shape.
- Structured data parses.

## What is not verifiable
- Whether a specific LLM will cite the page. No skill can promise this.
- Ranking uplift in AI Overviews. Google's own guidance says AI Overviews rest on the classic ranking systems (RAG over the Search index) — good SEO still matters, but no skill can prove a ranking outcome.
- The exact effect of `llms.txt`. Google publicly says it does not use it. Other LLMs may.

## What the skill produces
- `PASS/WARN/FAIL/NOT_VERIFIED` on the verifiable items above.
- Honest wording in messages. No promises of citation.
- Findings flagged `heuristic` where the evidence is a pattern, not a probe.
