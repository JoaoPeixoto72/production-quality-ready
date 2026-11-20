# SEO Audit v1 — Methodology

## 1. Evidence classes

| Class | Meaning |
|---|---|
| `machine_verified` | Verified by a direct probe (HTTP request, XML parse, JSON-LD parse, PSI API). |
| `heuristic` | Supported by strong indicators; not a full proof (regex on HTML, first-paragraph answerability heuristic). |
| `manual` | Requires human editorial judgment (E-E-A-T, tone, factual accuracy of copy). |
| `not_verified` | Insufficient access, network failure, or missing credentials. |

## 2. Status model

| Status | Use when |
|---|---|
| `PASS` | The control was verified with proven evidence. |
| `FAIL` | Concrete evidence of a defect or missing mandatory control. |
| `WARN` | Real but non-blocking risk, or evidence is heuristic. |
| `NOT_VERIFIED` | Access or evidence is insufficient. |
| `NOT_APPLICABLE` | The control does not apply to the target. |

## 3. Severity model

`Critical`, `High`, `Medium`, `Low`. A severity orders the fixes; it carries no
weight.

## 4. No score

The engine prints the counts per status and a verdict, never a number out of
100: a score hides which control failed, and the plugin's contract forbids one
(`CONTRACTS §7.2`). `NOT_APPLICABLE` is left out of the counts that decide the
verdict; `NOT_VERIFIED` lowers confidence and can force `PARTIAL_AUDIT`.

## 5. Release verdict rules

1. Any critical `FAIL` with `machine_verified` evidence → `BLOCKED`.
2. Any non-critical `FAIL` in material SEO gates (missing sitemap, noindex on production, broken canonicals) → `FIX_BEFORE_LAUNCH`.
3. No blockers but material unknown coverage → `PARTIAL_AUDIT`.
4. Otherwise → `READY_WITH_FOLLOWUPS`.

## 6. Anti-false-positive rule

Heuristic checks never emit a critical `FAIL` on their own. A heuristic pattern match downgrades to `WARN` with a clear reason. Only probes that prove the defect (HTTP status, DOM parse, JSON-LD parse) can raise `FAIL` at critical severity.

## 7. Honesty rules on GEO / AI search

- Do not present GEO / LLM visibility as guaranteed. Cite the specific check and what it does not prove.
- `llms.txt` is informational. Google publicly states it does not use it for ranking. Some LLM crawlers may. This skill treats it as `WARN` at most.
- Do not recommend removing existing `FAQPage` schema. Do not recommend adding `FAQPage` for SERP benefit — Google retired FAQ rich results in May 2026.
- Do not claim confirmed LLM citation benefit from any schema type.

## 8. A critical needs `machine_verified`

Severity and evidence are independent axes. A finding carries an
`evidenceClass` (`machine_verified`, `heuristic`, `manual`, `not_verified`), and:

- A **critical** `FAIL` requires `machine_verified` evidence (an HTTP status, a
  DOM/XML/JSON-LD parse, a CrUX/PSI field number). A heuristic match is
  downgraded to `WARN` — never a critical `FAIL`.
- A **critical** `PASS` likewise requires `machine_verified` evidence. A lab CWV
  number is `heuristic`; only field data (CrUX) or a declared measurement closes
  a critical CWV pass.
- `NOT_VERIFIED` is never rewritten to `PASS` by omission.

This is the same rule the plugin enforces everywhere: `PASS` needs a trace
(`CONTRACTS §4.6`), and a heuristic cannot carry a critical verdict.

## 9. External SEO data

The engines here are crawl-based. Live data (keyword research, backlinks,
local/maps, field CWV, LLM citation tracking) only an external provider has, and
this owner never reimplements it. Field Core Web Vitals reach the gate through
the project's declared `core-web-vitals-command` (`adapter-hints`); without it
`web.core-web-vitals` stays `NOT_VERIFIED`. Everything else a provider returns —
including any 0-100 score — is read as a **finding**, never turned into a
`PASS`. Providers and how to wire them: `references/seo-external-data.md`.

## 10. Regression (baseline)

`web.seo-no-regression` compares the current `seo-audit-report.json` against a
committed baseline (`scripts/seo_baseline.py`). A finding that was `PASS` and is
now `FAIL`, or a new `FAIL`, is a regression. Like the maintainability ratchet,
existing debt may not grow.
