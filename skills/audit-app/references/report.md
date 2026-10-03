# Report

**Hierarchy.** The output format of `audit-app`: the operational translation of
`CONTRACTS.md`'s aggregation and verdict rules (§7 gates, §4.3 coverage) into a
human report. `CONTRACTS.md` is authoritative.

- "Module" (here) = "owner" (`CONTRACTS.md`).
- "Obligation" (here) = "canonical check" (§7.4).
- "Critical gate" (here) = "check with a predicate in a declarative gate" (§7.1).
- The `X/Y` coverage fraction = §4.3.1 (required).

The report covers **the modules requested**, not every one that exists.

## Required opening

```markdown
## 1. Result
<module>: Product: PASS | CONCERNS | FAIL · Coverage: COMPLETE | PARTIAL | BLOCKED (X/Y)
— one sentence of justification.
(The fraction is of critical gates resolved, and is required: `BLOCKED (0/8)`
is not the same audit as `BLOCKED (7/8)`.)
(One pair per module run. Global only in `full`, by the SKILL.md aggregation rules.)

## 2. Scope
Request: "<the user's request>"
Modules run: <list>
Auxiliary references opened: <list, or none>
Modules not run: <list, with a reason>
Interpretation: <only if the request was ambiguous — the choice made, in one sentence>

## 3. Evidence
Contract: SHA-256 <digest>   (`python scripts/validate_report.py --contract`)
Commit: <short sha>  Tree at start (t0): clean | dirty (<n> files)
Tree at end (t1): same | CHANGED (<paths> — and what that invalidated)
Environment: <OS, versions read from the lockfiles>
Capability: INTERACTIVE | ASSISTED | STATIC
Commands: <command — cwd — exit code>
  (The exit code is copied from the terminal when the command ran, never from
  memory or expectation: nothing checks it afterwards.)
Unavailable tools: <tool — exact error>
Artefacts: /tmp/audit-<date>/
This report: docs/audits/<date>-<scope>.md

## 4. Verification
Critical gates: X/Y resolved
Total obligations: X/Y resolved
PROVEN: n · CLEARED: n · UNPROVEN: n · NOT_APPLICABLE: n
(Counted **in** the obligations table, never estimated. If summary and table
disagree, the summary is wrong — and a wrong `PROVEN` is a wrong verdict.)

## 5. Coverage conclusion
What this report proves, in two or three sentences.
What remains unknown, and why.
```

Direct evidence of data loss, arbitrary execution, a compromised update or
exposed credentials — even out of scope — goes **before** block 1, headed
`CRITICAL RISK`.

## Obligations table (required)

Before the findings. Counts alone allow nothing to be verified; this table is
what makes the audit auditable.

```markdown
## Obligation results

| ID | State | Gate | Evidence | Coverage | Artifact | Note |
|---|---|---|---|---|---|---|
| UX-01 | CLEARED | yes | EXECUTION | COMPLETE | captures/ux-01-* | the 12 mapped flows, all walked |
| UX-02 | PROVEN | yes | EXECUTION | COMPLETE | captures/ux-02-cancel | see UX-F01 |
| UX-06 | UNPROVEN | no | — | — | — | tokens unreadable without a build |
| RUST-02 | UNPROVEN | yes | STATIC_ANALYSIS | SAMPLE | — | the worker's `catch_unwind` tested; the ~190 `unwrap`/`expect` in `tools`/`editor` not opened |
| A11Y-08 | NOT_APPLICABLE | no | READING | COMPLETE | — | no own zoom, no animations — both absences confirmed |
```

Every activated obligation appears, critical gates first. **No row stays
`PENDING`**: not verified is `UNPROVEN`, with the reason in Note.
`OUT_OF_SCOPE` is not an obligation state — it belongs to detections and areas.

**One state per row, no modifiers** (`SKILL.md`); the Coverage column says how
much of the universe the evidence looked at (`contract-and-evidence.md`). State
× Coverage is read as a pair: the `RUST-02` row is the difference between "this
is fine" and "this is fine in the part I opened".

## Findings

One per root cause, never one per symptom.

```markdown
### <ID> — <title: the defect, not the suggestion>

- **State**: CONFIRMED
- **Priority**: P0 | P1 | P2 | P3
- **Confidence**: HIGH | MEDIUM | LOW (LOW only in P2/P3 — see below)
- **Area**: <module>
- **Platform**: all | Windows | macOS | Linux
- **Location**: `path:line`
- **Flow**: <which mapped flow>
- **Trigger**: <the concrete sequence that causes it>
- **Execution path**: <UI → hook → invoke → command → ...>
- **Root cause**: <what is wrong, not the symptom>
- **Consequence**: <what happens to the user or buyer>
- **Evidence**: <type> — <what was observed>
- **Existing test**: <what exists today, or NO_TEST>
- **Related decision**: <the comment beside the code, or the line in the agent's map, that decides it>
- **Minimal fix**: <the smallest change that solves it>
- **Required verification**: <how to prove it is solved>
- **Effort**: <order of magnitude>
- **Dependencies**: <findings that must come first>
```

Stable IDs: module prefix and number (`SEC-F01`, `UX-F03`). A finding that
already existed in an earlier audit reuses its ID and is marked as a
**recurrence**.

**Numbers come from the baselines, not the report.** `resolved-findings.md`,
`accepted-risks.md` and `last-audit.md` are the only memory of which numbers
are taken — phase 0 reads them and phase 4 proposes writing them. A taken
number is either the same defect again (say recurrence) or another one (the
next free number). Reusing it silently breaks `resolved-findings.md`'s key;
`validate_report.py` rejects it. Until the baselines are written, the memory
does not exist and the next audit restarts at `F01`.

**Title**: describes the defect. "Cancelling an export leaves FFmpeg running" —
not "improve cancellation".

## Priorities

| P | Criterion |
|---|---|
| `P0` | Exploitation, widespread data loss, or compromised distribution |
| `P1` | Prevents selling: serious failure in a main flow, persistent unavailability, or a legal impediment |
| `P2` | Material defect, or debt already causing recurring cost |
| `P3` | Localised improvement, polish |

An open P0 or P1 gives `FAIL`. No P1 is compatible with `PASS` or `CONCERNS`:
if the consequence does not prevent selling, it is P2. A formally accepted P1
leaves the active findings for `ACCEPTED_RISK`, with an entry in
`baselines/accepted-risks.md` — a known but unapplied mitigation does not count.
**`P0` never becomes `ACCEPTED_RISK`**: it is fixed, not accepted to reach `PASS`.

Do not inflate P0/P1: if everything is critical, nothing is. More than a few P3
means the audit drifted into style review; group them by common cause. **Do not
list what is fine**, except to bound a risk.

## Precautionary alerts

A serious suspicion without enough proof is **not** a `CONFIRMED` P0/P1. It goes
in its own section, right after the opening:

```markdown
## PRECAUTIONARY ALERT — to confirm
<what was observed> · <why it could be serious> · <what is missing to confirm>
```

`LOW` confidence **never sustains a P0/P1 finding**: that case always comes
here. In `P2`/`P3`, `LOW` is allowed directly in the finding
(`contract-and-evidence.md`).

## Hypotheses

After the findings, without priority. Candidates that did not pass the funnel
but deserve investigation, each with **the measurement or test that would
confirm it**.

## Closing

```markdown
## Blockers to selling
<the P0/P1 that prevent charging money for this>

## Where to start
<order by dependencies and risk reduction, not pure priority. A P2 that
unblocks three P1s comes first.>

## Out of scope
<OUT_OF_SCOPE detected — one line each, with the recommended module>

## Not verified
<UNPROVEN, with the concrete reason and what it would take>
<NOT_APPLICABLE, with the justification>

## Checklist: X/Y  (critical gates: X/Y)

## Residual risks
<what remains unknown after this audit>

## To record in the baselines
<block ready to paste into last-audit.md, and new entries for
resolved-findings.md and accepted-risks.md — proposed, not written>
```

## Mistakes not to make

- Writing "it seems" without saying whether it is fact, inference or hypothesis.
- Prioritising an item whose consequence was not described.
- Repeating one cause in three findings because it has three symptoms.
- Recommending a tool without pointing at the defect it solves here.
- Ending without the obligations table, the `Checklist`, or the `UNPROVEN`.
- Summarising counts "roughly" instead of counting them in the table.
- Inventing compound states (`CLEARED (decision)`) instead of picking one and
  putting the rest in Note.
- Closing a universal obligation with `SAMPLE` coverage evidence.
- Giving `CLEARED` to an unmet obligation because a decision justifies it.
- Reporting `BLOCKED` coverage without the fraction and without what unblocks it.
- Applying fixes. The audit ends at the report.
