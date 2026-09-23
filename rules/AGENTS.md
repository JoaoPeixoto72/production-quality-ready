# production-quality-ready — rules for the agent

1. **One subject, one owner, one rule.** Every quality subject has one
   owner and a binary criterion (`PURPOSE.md §4`).
2. **Evidence is a file, not a call.** No skill invokes another. Owners
   write `.audit/<owner>/<producer>--<check>.evidence.yaml`.
3. **A PASS needs `command:` and `log:`.** Reading code never passes a
   check (`CONTRACTS.md §4.6`).
4. **The orchestrator only reads.** `audit-app` applies the gates in
   `<host>/gates.json` and runs nothing.
5. **Gate, never a score.** Missing proof is `BLOCKED (n/m)`, not approval.
6. **Work cycle**, through the project's adapters: open with
   `start-work`, review with `review-change`, close with `close-work`,
   prove in the running app with `verify`.
