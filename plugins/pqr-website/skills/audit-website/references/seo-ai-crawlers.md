# AI crawlers — the taxonomy, and the claim each bot supports

Managing AI crawlers in `robots.txt` is a **decision the project makes**, not a
default. The skill reports the policy it finds; it never scores "AI readiness"
off a single token, because the bots govern different capabilities and the
claim you make must match the bot you checked.

## The crawlers

| Crawler | Owner | Purpose | Obeys `robots.txt`? |
|---|---|---|---|
| `GPTBot` | OpenAI | **Model training only** (not ChatGPT Search) | yes |
| `OAI-SearchBot` | OpenAI | **ChatGPT Search citability** | yes |
| `ChatGPT-User` | OpenAI | Browsing on a user's behalf (user-triggered) | "may not apply" (user-triggered) |
| `ClaudeBot` | Anthropic | **Model training only** (not Claude search) | yes |
| `Claude-SearchBot` | Anthropic | **Claude search citability** | yes |
| `Claude-User` | Anthropic | Browsing on a user's behalf (user-triggered) | yes (Anthropic: all three honor it) |
| `PerplexityBot` | Perplexity | Perplexity search index (not foundation-model training) | yes |
| `Perplexity-User` | Perplexity | Fetches for a user's question (user-triggered) | generally ignores |
| `CCBot` | Common Crawl | Open dataset / training data | yes |
| `Bytespider` | ByteDance | Training | yes |
| `cohere-ai` | Cohere | Cohere models | yes |
| `Google-Extended` | Google | **Gemini/Vertex training & grounding, and training of the models behind Search gen-AI features** (not Search inclusion or ranking) | yes |
| `Google-CloudVertexBot` | Google | Site-owner-requested Vertex AI Agent crawls | yes |
| `Google-Agent` | Google | User-triggered agent fetches (agentic browsing) | **no** (user-triggered) |
| `Google-GeminiNotebook` | Google | Fetches user-added source URLs (replaced `Google-NotebookLM`) | **no** (user-triggered) |
| `Applebot-Extended` | Apple | **Apple Intelligence / generative-AI training opt-out only** (not Siri, Spotlight, Safari; does not itself crawl) | yes |

Sources: OpenAI bots docs, Google crawlers overview, Anthropic crawler support
article, Apple Applebot-Extended support article. Anthropic's current article
lists only `ClaudeBot`, `Claude-User` and `Claude-SearchBot`; the older
`anthropic-ai` token is not documented and is not asserted here.

The `Obeys robots.txt?` column is what each operator **documents**; compliance is
not independently verified here, and some operators' behaviour (notably
`Bytespider`) is disputed by site owners — do not build a claim on it.

## Check the right bot for the claim you are making

Two pairs are routinely conflated. **Each claim may only be supported by its own
bot's status** — check and report them separately.

| Claim | Bot to check | Bot that does **not** support the claim |
|---|---|---|
| "citable in ChatGPT Search" | `OAI-SearchBot` | `GPTBot` |
| "available for OpenAI training" | `GPTBot` | `OAI-SearchBot` |
| "citable in Claude's search features" | `Claude-SearchBot` | `ClaudeBot` |
| "available for Anthropic training" | `ClaudeBot` | `Claude-SearchBot` |
| "eligible for Google Search / AI Overviews / AI Mode" | `Googlebot` | `Google-Extended` |
| "usable for Gemini/Vertex training & grounding" | `Google-Extended` | `Googlebot` |
| "discoverable via Siri/Spotlight/Safari" | `Applebot` | `Applebot-Extended` |
| "opts out of Apple Intelligence training" | `Applebot-Extended` | `Applebot` |

**Honesty rules (a claim on the wrong bot is a false finding):**

- A blocked `Google-Extended` is **never** evidence a site is missing from
  Google Search — Search, AI Overviews and AI Mode are served from the
  `Googlebot` index. Report `Google-Extended` as a *training/grounding* control only.
- `GPTBot` says nothing about ChatGPT Search citability; only `OAI-SearchBot`
  does. A site that blocks `GPTBot` and allows `OAI-SearchBot` is fully citable
  in ChatGPT Search.
- `ClaudeBot` says nothing about Claude search citability; only
  `Claude-SearchBot` does.
- `Applebot-Extended` is a training opt-out label, not a crawler; blocking it
  leaves Siri/Spotlight/Safari discovery intact while `Applebot` is allowed.

## User-triggered fetchers ignore `robots.txt`

`Google-Agent`, `Google-GeminiNotebook` and Google Messages are user-triggered
and **cannot be blocked via `robots.txt`**; OpenAI says `robots.txt` "may not
apply" to `ChatGPT-User`; Anthropic's `Claude-User` honors it. Use server-side
access controls for those, not `robots.txt`.

Emerging: **Web Bot Auth** — an experimental protocol (IETF draft) built on
HTTP Message Signatures (RFC 9421) — lets bots authenticate with a
`Signature-Agent` header and a key directory; Google is experimenting with it
under the `agent.bot.goog` identity. Reverse-DNS verification remains the
fallback.

## Example: allow search indexing, block training crawlers

```
# Allow search indexing and AI search citability, block AI training
User-agent: GPTBot
Disallow: /

User-agent: Google-Extended
Disallow: /

User-agent: CCBot
Disallow: /

User-agent: Bytespider
Disallow: /

User-agent: *
Allow: /
```

Blocking an AI **search** crawler (`OAI-SearchBot`, `Claude-SearchBot`,
`PerplexityBot`) removes the site from that engine's answers. Never promise
traffic from allowing one either — the skill reports the policy, not an outcome.

## What the skill checks

- The `robots.txt` decision for each crawler above is **explicit** (an unstated
  policy is a finding, not a pass).
- No claim is made on the wrong bot (see the matrix).
- A `5xx` on `robots.txt` is a critical finding: compliant crawlers read it as
  "disallow everything".
