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

| Severity | Weight |
|---|---:|
| `Critical` | 10 |
| `High` | 6 |
| `Medium` | 3 |
| `Low` | 1 |

## 4. Scoring rules

- `FAIL` consumes full weight.
- `WARN` consumes 40% of weight.
- `NOT_APPLICABLE` is excluded from the denominator.
- `NOT_VERIFIED` is excluded from score but lowers confidence and can force `PARTIAL_AUDIT`.

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
