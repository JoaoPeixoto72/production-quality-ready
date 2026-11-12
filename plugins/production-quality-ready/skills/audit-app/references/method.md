# Method — H · V · T · C

The audit asks one question in five ways. Everything else is a detail.

## Ontology

- **Baseline** — requirements / intended behaviour. Source of truth.
- **H — Horizontal:** does the app work correctly through each flow?
- **V — Vertical:** is each layer solid on its own?
- **T — Temporal:** does it stay correct as state changes over time?
- **C — Cross-audit:** where do H, V and T contradict each other?
- **Contracts** — the boundaries UI↔state↔service↔API↔backend↔DB↔external.
- **Execution paths** — what actually happens, from bootstrap onwards.
- **Cross-cutting concerns** — security, performance, accessibility,
  observability, i18n, UX, resilience, data, compliance/GDPR. Properties
  verified on the relevant axes, not an axis of their own.

## Phases

| Phase | Focus | Deliverable |
|---|---|---|
| 1. Reconnaissance | Baseline, H, V, T | Inventory; architecture, flow, state and contract maps |
| 2. Risk | — | Flows, layers and transitions prioritised P1/P2/P3 |
| 3. Horizontal | H | Report per flow |
| 4. Vertical | V | Report per layer |
| 5. Temporal | T | Transition report |
| 6. Cross-audit + cross-cutting | C + X | Evidence Matrix |
| 7. Execution paths + dynamic testing | H+V+T | Reproducible evidence |
| 8. Report + cycle | — | Executive + technical; re-test and regression audit feed back into the matrix |

Adapt the order and depth to risk. In a large system, split H, V and T across
parallel subagents and do the cross-audit yourself.

## Status scale

| Symbol | Status | Requires |
|---|---|---|
| ✓ | PASS | Evidence that it passed |
| ✗ | FAIL | A finding ID |
| ⚠ | PARTIAL | What was left uncovered |
| ? | UNKNOWN | What remains to verify, and why |
| — | N/A | Justification |
| ○ | COND | The condition under which it applies |

Not verified is not passed.

## Cross-cutting concerns by axis

| Concern | H | V | T |
|---|---|---|---|
| Security | ✓ | ✓ | ✓ |
| Performance | ✓ | ✓ | ✓ |
| Accessibility | ✓ | ✓ | ○ |
| Observability | ✓ | ✓ | ✓ |
| i18n | ✓ | ✓ | ○ |
| UX | ✓ | ✓ | ✓ |
| Resilience | ✓ | ✓ | ✓ |
| Data | ✓ | ✓ | ✓ |
| Compliance/GDPR | ✓ | ✓ | ○ |

## Bug classes

- **Direct** — lives on a single axis.
- **Hard** — lives at the intersection of axes.
- **Systemic** — spans multiple flows, layers or components. Systemic ≠ cross-cutting.
- **Invisible** — lives where nobody checked. The `?` cells map these.

## Severity

| Level | Security | Functional | Deadline |
|---|---|---|---|
| 🔴 Critical | RCE, auth bypass, sensitive data exposed | Data loss/corruption, critical flow blocked | 24–72h |
| 🟠 High | IDOR, stored XSS, authorization failure, critical race | Incorrect result in a P1 flow, no workaround | 1–2 weeks |
| 🟡 Medium | Info disclosure, CSRF, headers, stale cache | Incorrect behaviour with a workaround | 1 month |
| 🟢 Low | Hardening, best practices | Minor inconsistency | Next cycle |

## Scope

Point (component/line) · Flow · Service (every flow that uses X) · App.
Priority = severity × scope. Always justify the final priority.

## Golden rule

- Baseline: is this what should happen?
- H: does the path work?
- V: is the layer solid?
- T: is the transition safe?
- C: where do these contradict each other?
- Cross-cutting: are the properties correct on each relevant axis?
- Contracts: are the boundaries compatible?
- Execution paths: what actually happens, from zero?
