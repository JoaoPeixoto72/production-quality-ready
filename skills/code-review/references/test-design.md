# test design — what makes a test a test

Reference for `code-review`'s `runtime.tests-have-oracles`, `diagnose`'s
regression step and `spec`'s "proof each criterion needs". It holds the
rule, not the tooling: how a case is written in this repo is the stack
reference's business.

## The one rule

**A test declares the risk it covers and the specific thing it would have
caught.** No declaration, no test: a case that asserts `status < 500` is a
smoke alarm, not a test. The declaration is what lets a reviewer see that
removing the fix turns it red.

## What a test must be able to say

| Sentence the test answers | Failure it shows |
|---|---|
| Which risk does this cover? | A test nobody can name a risk for covers none. |
| What specific thing does it catch? | "It didn't throw" catches nothing. |
| Would it fail without the change? | If it passes on the pre-change commit, it is not covering this change. |
| Which single behaviour does it pin? | Several behaviours per case hide which one broke. |

## Grades

- **A** — the risk is named, the oracle is specific, and the case fails on
  the pre-change commit. This is the only accepted grade.
- **B** — the case runs the code and asserts it did not blow up. Rewritten,
  not deleted: keep the scenario, add the oracle.
- **C** — no case at all, with "it compiles" or "it is in the README" as
  the argument. Blocks (`CONTRACTS.md §4.6`).

## Oracles that hold

- An exact value: `409`, `0`, the 7th row, the total to the cent.
- An invariant over a set: no duplicate ids, sum of debits equals sum of
  credits, every key present in both locales.
- An ordering: the second call sees the first call's write.
- A message contract: the field names and types the other side reads.

## Oracles that do not

- The absence of an exception, or "it returned something".
- A snapshot taken after the change: it records whatever the code did.
- A sleep followed by an assertion on "eventually".
- The same expression on both sides (`expect(f(x)).toBe(f(x))`).
- A mock asserting that the mock was called — that tests the test.

## Determinism

A test that fails on the second run costs more than the bug it found.

- No wall-clock dependence: inject the clock, do not read it.
- No unsynchronised concurrency: assert on the interleaving you forced, or
  on the outcome that all interleavings must reach.
- No shared mutable fixtures between cases; build the state the case needs.
- No network in a unit case; the boundary is stubbed in bad faith
  (`code-review` A8/A4 patterns).

## One case per behaviour, and the name says which

The name is read in a failure report, at 3 a.m., by someone who did not
write it. Name the behaviour and the condition, not the function:
`refund_of_paid_order_returns_signature_error`, not `test_refund_2`.

## Mutation, the cheap check

Break the fix on purpose — invert the condition, delete the guard, return
the old value — and run the case. It must go red. Restore the fix. This is
`runtime.tests-have-oracles` in one move, and it takes less time than
arguing about whether the test is real.
