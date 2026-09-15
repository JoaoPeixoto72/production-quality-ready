---
name: review-change
description: "Review a change before calling it done. Runs the change through this project's invariants declared by the adapter — reuse, layers, contracts between parts, UI/UX rules, process and path boundaries — and says what to run to prove it's right. Universal contract; each project supplies the adapter. Use after writing or changing code, before close-work. Do NOT use to audit the whole app — that's audit-app. Do NOT use to open a work session — that's start-work."
contract: CONTRACTS.md
evidence-schema: "1.3.x"
requires-adapter: true
adapter-contract: adapter-contracts/review-change.md
version: 1.0.0
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---

# review-change

Universal contract for reviewing a change before commit. This is the
last honest checkpoint between "code written" and "close the task"; when
it skips, defects that live inside the change (broken invariants,
architectural drift, missed retry, unsafe input) reach the audit as
noise you now have to sort back out.

## Founding rule: this project's invariants, not the world's

This skill does not carry a generic checklist. It carries **the local
adapter's list of invariants that this project already paid for once** —
each with the concrete example that motivated it. Any generic rule (UX,
accessibility, IPC, security) lives in the plugin's owner and gets cited
by name, not copied.

## Order

1. **Read the diff.** Nothing else, first.
2. **Run each invariant.** The adapter enumerates them; each has an
   example.
3. **Cite the plugin owner** for anything the adapter didn't cover:
   - UI/UX / accessibility → `design-pro`;
   - contracts between processes / API / IPC → `code-review-contract`;
   - runtime: concurrency, panic, tests → `code-review-runtime`;
   - security / input-not-trusted → `security-audit`;
   - performance budgets → `performance-audit`;
   - persistence / migration → `reliability-audit`.
4. **Say what to run to prove it.** The proof command from the adapter,
   with the format for numbers.

## Contract for the local adapter

Numbered project invariants, each with the example that motivated it.
Proof command. Explicit cross-references to plugin owners.

See `adapter-contracts/review-change.md`.
