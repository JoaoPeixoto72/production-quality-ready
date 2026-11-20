# External SEO data — declare it, don't reimplement it

The two engines here crawl a public surface. Real SEO work needs live data the
crawl cannot produce — keyword research, backlinks, local/maps, field Core Web
Vitals, LLM-citation tracking. This skill **consumes** that data; it never
reimplements a provider. Naming a
provider here is a *recommendation*, not an assumption: the project still
declares what it uses, and the plugin runs on any host (Claude Code, Antigravity,
Codex) without it.

## How it reaches the gate

Field Core Web Vitals are the one provider number that settles a check. The
project declares the command that measures them in `gates.json`:

```json
"adapter-hints": {
  "core-web-vitals-command": "node ~/seo-tool/bin/cwv.js --url $SITE --fail-on-poor"
}
```

The runner runs it: exit 0 is `PASS`, non-zero is `FAIL`, and both carry the
command and its log. Without it `web.core-web-vitals` stays `NOT_VERIFIED` — the
gap is said, never filled. Everything else a provider returns (keywords,
backlinks, GEO visibility, a 0-100 score) is read by the auditor as a
**finding, not a gate**: scores are consumed, never turned into a `PASS`
(`references/seo-methodology.md` §9).

## Providers that fit (examples, not endorsements)

These are known to produce the data above — pick what the project uses, leave
the rest out.

| Provider | Adds | Shape |
|---|---|---|
| **claude-seo** (`AgriciDaniel/claude-seo`) | broad SEO toolkit: technical, GEO/AEO, backlinks, local, e-commerce, SXO; field data through its MCP extensions (DataForSEO, Ahrefs, CrUX/GSC, Matomo) | Claude Code plugin; emits a report + JSON |
| **DataForSEO** / **Ahrefs** / **SE Ranking** | SERP, backlinks, keyword research, LLM visibility | paid API |
| **Google PSI / CrUX** | field Core Web Vitals — the `machine_verified` number a critical CWV pass needs | free API (`--psi-key`) |
| **GSC / GA4** | indexation, organic traffic, queries | OAuth |
| **Matomo** | self-hosted analytics | API |

`claude-seo` is itself a Claude Code plugin. On another host, use whatever
command produces the same data — the **evidence** is what matters, not the
tool. The plugin must not assume a project has any of these.

## What stays here

The gate, the evidence discipline (`PASS` = `command`+`log`), the SARIF output,
the drift baseline, and the checks a crawl *can* prove. The provider does the
SEO; this owner decides.
