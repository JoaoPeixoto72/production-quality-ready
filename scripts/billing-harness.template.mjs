// billing-harness.template.mjs — the six sales paths, in the `commercial-readiness` format.
// Copy into the project, implement each scenario with its test library, and declare one command per
// scenario in `adapter-hints.billing-harness-commands` (keys `sell-01-activation` … `sell-06-end-of-payment`,
// e.g. "node tests/billing-harness.mjs --only sell-01"). A line without a command is NOT_VERIFIED.

const only = process.argv[process.argv.indexOf("--only") + 1] || "all";
let pass = 0, fail = 0;
const check = (name, ok, detail = "") => {
  ok ? pass++ : fail++;
  console.log(`  ${ok ? "OK  " : "FAIL"} ${name}${detail ? " | " + detail : ""}`);
};

// sell-01 — checkout → webhook → active entitlement; a duplicate webhook does not duplicate
if (only === "all" || only === "sell-01") {
  check("sell-01-activation", false, "to implement: checkout, webhook, entitlement");
}

// sell-02 — payment provider down: the user keeps access through the declared grace, nothing half-written
if (only === "all" || only === "sell-02") {
  check("sell-02-offline-or-failure", false, "to implement: failure + grace");
}

// sell-03 — change email / transfer ownership / add a seat without losing data or access
if (only === "all" || only === "sell-03") {
  check("sell-03-machine-or-account-change", false, "to implement: account change");
}

// sell-04 — free → paid without losing data; proration and tax to the cent
if (only === "all" || only === "sell-04") {
  check("sell-04-trial-to-paid", false, "to implement: trial -> paid");
}

// sell-05 — refund and cancellation; access revoked at once on refund
if (only === "all" || only === "sell-05") {
  check("sell-05-refund-cancel", false, "to implement: refund + cancellation");
}

// sell-06 — end of payment: declared grace, then read-only or export; data never held hostage
if (only === "all" || only === "sell-06") {
  check("sell-06-end-of-payment", false, "to implement: end of period");
}

console.log(`\nFAILURES: ${fail}`);
process.exit(fail === 0 ? 0 : 1);
