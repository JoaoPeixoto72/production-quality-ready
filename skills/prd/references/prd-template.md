# PRD, CLAUDE.md and regression log — templates

Write the generated files in the owner's language. Omit every field that does
not apply. IDs are stable: never renumber.

## `PRD.md`

````markdown
# PRD — [App name]

Version: [0.1]
Status: [Draft / In review / Approved]
Owner: [who decides]
Date: [YYYY-MM-DD]

Only confirmed decisions go here. What is still undecided goes to section 7.
Update when a product decision changes; record the reason and approval of
relevant changes in the commit, the review request or this document.

## 1. Problem and users

Problem: [what real difficulty exists]
Users: [who has it, in what context]
Today's solution and its limits: [how they cope, where it fails]
Proposal: [the app lets them get ______ without needing ______]

## 2. v1 goals

| ID | Expected result | How to verify | Target, if any |
|----|-----------------|---------------|----------------|
| O-01 | | | |

Solving the problem is not shipping features. Do not invent targets; if one is
needed, say in section 7 how it will be set.

## 3. v1 scope

### Mandatory
### Desirable — can be postponed
### Out of scope

## 4. Roles and permissions

| Role | Can do and see | Cannot do or see |
|------|----------------|------------------|

When applicable: creating, suspending and recovering accounts · stacking of
roles · separation of data between people, teams, organisations.
If access varies by field: a second table (field, who sees, who changes,
condition).

## 5. Flows and acceptance criteria

Repeat per flow.

### F-01 — [Flow name]

Goal: [O-01] · Priority: [Mandatory / Desirable] · User: [role]
Preconditions: [what must exist first]

Path:
1. …

Result: [observable end state and the data kept]
Rules: [validations, limits]
Failures and edge cases:
- If [condition], then [behaviour, message shown, recovery, data kept or lost].
- Concurrency, if applicable: [two actions on the same resource].
- Repetition, if applicable: [double click, resend, retry after failure].
Messages: [exact text when it is a product decision; otherwise what it must say]

Acceptance criteria:
- F-01/CA-01: Given [context], when [action], then [result].
- F-01/CA-02: [a relevant failure].
- F-01/CA-03: [permissions, when applicable].

Visual reference, if needed: [link or file]
Outside this flow: […]

## 6. Cross-cutting rules and constraints

Do not repeat what a flow already says. Each requirement must be verifiable
(`T-01`, …).

### Data and privacy
Data collected and purpose · sensitive data and protection · retention,
deletion, export · legal duties confirmed · legal duties to validate (→ §7).

### Conditions of use
Platforms and devices · language, currency, time zone · data volume and
concurrent use · performance required, measured how · accessibility required,
verified how · behaviour on failure, persistence, recovery.

### Integrations
| System | Purpose | Data exchanged | If it fails |
|--------|---------|----------------|-------------|

### Confirmed constraints
[Budget, deadline, environment, mandatory technology — always with the reason.]

### Relevant risks
| Risk | Impact | Mitigation |
|------|--------|------------|

### Critical paths
[Flows essential to the app's goal, or whose failure could cause improper
access, data loss, financial harm or irreversible effects.]

### Glossary — if needed
| Term | Meaning in this product |
|------|-------------------------|

## 7. Pending decisions and assumptions

| ID | Question | Who decides | Blocked feature or action |
|----|----------|-------------|---------------------------|
| D-01 | | | |

Do not implement the blocked part until decided; the rest may proceed.

| ID | Hypothesis | How to validate | Impact if wrong |
|----|------------|-----------------|-----------------|
| P-01 | | | |

Assumptions are not requirements. Validate before implementing when the
impact is relevant.

## 8. Approval conditions

### Ready to implement a slice
- Scope and expected result are defined.
- Rules, permissions and acceptance criteria are clear.
- The decisions and assumptions that block this slice are resolved.
- There is a defined way to verify the result.

Doubts that only affect other slices need not be resolved.

### Ready to accept a delivery
- Mandatory flows meet their acceptance criteria.
- Permissions verified, including direct unauthorised access.
- Relevant failure, concurrency and repetition cases verified.
- Data persists and is recovered as defined.
- Agreed cross-cutting requirements verified.
- Main paths verified in the running app.
- Tests and regression passed on the candidate version, with evidence linked
  to the criterion IDs.
- Critical paths verified again.
- No blocking defects; limits and coverage risks documented.
- Run instructions work.
- The owner approved the result.

Blocking defect: [what prevents accepting this app]
````

## `CLAUDE.md`

When the plugin is installed, replace "Verification and regression" and
"Test changes" with one line each naming `verify`, `review-change` and
`close-work`.

````markdown
# Project instructions

## Product
- Read the scope, the relevant flow, the cross-cutting rules and the blocking
  decisions in PRD.md.
- Do not invent requirements or treat assumptions as confirmed decisions.
- Ask only what blocks the current work.
- Ask approval for scope changes, high-impact decisions and risky or
  irreversible actions.
- Record the reason and approval of relevant product changes.

## Commands
- Run: [command] · Tests: [command] · Build: [command] · Lint: [command]

## Repository specifics
- [Only conventions specific to this project.]

## Dependencies
- Before adding a dependency, present name, purpose, origin, version and
  relevant implications, and ask approval.
- Confirm the package and version identity in the authorised registry or
  repository, and the link to the expected documentation or project.
- Age, usage and maintenance are review signals, not guarantees.
- Approval may cover a previously agreed list; reinstalling approved pinned
  versions needs none.

## Verification and regression
- Keep implementation, test results, functional verification and owner
  approval apart.
- Do not claim verifications you did not run. Passing unit tests do not prove
  the full path works.
- Without access to the interface, leave "Awaiting manual verification" with
  actions and expected results; record manual confirmation only after the
  owner answers.
- After the first verification, automate critical and repeated paths when
  feasible; if not, explain why and propose a manual alternative and
  frequency for approval.
- Run the regression of affected flows and their dependencies; re-verify the
  critical paths before each delivery.
- Record coverage, tested version and evidence in tests/REGRESSION.md. With
  uncommitted changes, record the base commit and a reference to the diff or
  snapshot. After later changes, repeat the affected verifications.
- Never attribute human approval to agent-reported results.

## Test changes
- Do not change tests to hide failures.
- If a change alters expected behaviour, removes cases or reduces coverage,
  explain and wait for approval. Technical fixes that preserve the check may
  be applied, explained and re-run.
- If a product decision changes, update the PRD and the matching tests.

## Security
- No secrets in versioned files. Do not disable protections to make tests pass.
- Ask confirmation before deploys, migrations or destructive operations.

## When finished
- Summarise changes, verifications, limits and pending work; update the slice
  plan if one exists; commit only when asked or authorised.
````

## `tests/REGRESSION.md`

````markdown
# Regression

## Coverage and last run

| PRD criterion | Method | Test or manual steps | Tested version | Date | Result | Evidence |
|---------------|--------|----------------------|----------------|------|--------|----------|
| F-01/CA-01 | Automated / Manual | | | | Pending / Passed / Failed | |

Tested version: commit, delivery version, or base commit + diff/snapshot ref.
Automated evidence: report or run result. Manual evidence: who ran it,
environment, observed result. Keep earlier runs in history or the reports
referenced.

## Paths kept manual
| Path | Reason | When to repeat | Approved by |
|------|--------|----------------|-------------|

## Coverage risks
- [What was not verified, impact, decision needed.]

## Delivery approval
[Reference to the owner's confirmation and the approved version.]

The agent may record results, never grant human approval. If a technical
barrier is needed, keep the approval in a record the agent cannot change.
````

## Optional: `plan/[slice].md`

Only when the slice's complexity or continuity justifies it.

````markdown
# Slice — [Name]

Requirements covered: [F-01, T-01]
## Expected result
## Plan
## Outside this slice
## Planned verification
| Criterion | Test or manual check |
Record results in tests/REGRESSION.md.
## State to resume
Implemented · verification pending · blocked by [D-01 / P-01 / none] · next
step · known limits
````

## First prompt to the agent

> Read the PRD and name what blocks the first working slice. Ask only the
> necessary questions. Propose the implementation and its verification, linking
> tests to acceptance criteria, and wait for my approval of that proposal
> before writing code. Make a separate plan only if complexity or continuity
> justifies it. Follow `CLAUDE.md`.
