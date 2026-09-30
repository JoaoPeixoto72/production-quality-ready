// billing-harness.template.mjs — os seis caminhos de venda, no formato do
// owner `commercial-readiness`.
//
// Copia para o projeto (ex.: `tests/billing-harness.mjs`), implementa os seis
// cenários com a biblioteca de testes que o projeto já usa, e declara em
// `.agents/gates.json` — **uma linha por cenário**:
//
//   "adapter-hints": {
//     "billing-harness-commands": {
//       "sell-01-activation": "node tests/billing-harness.mjs --only sell-01",
//       "sell-02-offline-or-failure": "node tests/billing-harness.mjs --only sell-02",
//       "sell-03-machine-or-account-change": "node tests/billing-harness.mjs --only sell-03",
//       "sell-04-trial-to-paid": "node tests/billing-harness.mjs --only sell-04",
//       "sell-05-refund-cancel": "node tests/billing-harness.mjs --only sell-05",
//       "sell-06-end-of-payment": "node tests/billing-harness.mjs --only sell-06"
//     }
//   }
//
// O que fica de fora **não** herda o PASS das outras: o instrumento devolve
// NOT_VERIFIED para a linha sem comando, com a razão dita. É a diferença entre
// "não testámos o caminho de reembolso" e "não há reembolsos".

const only = process.argv[process.argv.indexOf("--only") + 1] || "all";
let pass = 0, fail = 0;
const check = (name, ok, detail = "") => {
  ok ? pass++ : fail++;
  console.log(`  ${ok ? "OK   " : "FALHA"} ${name}${detail ? " | " + detail : ""}`);
};

// sell-01 — checkout → webhook → entitlement ativo; webhook duplicado não duplica
if (only === "all" || only === "sell-01") {
  check("sell-01-activation", false, "implementar: checkout, webhook, entitlement");
}

// sell-02 — indisponibilidade do fornecedor de pagamento: o utilizador mantém
// o acesso durante a tolerância declarada, e nada é escrito a meio
if (only === "all" || only === "sell-02") {
  check("sell-02-offline-or-failure", false, "implementar: falha + tolerância");
}

// sell-03 — mudar de email / transferir titularidade / adicionar lugar sem
// perder dados nem acesso
if (only === "all" || only === "sell-03") {
  check("sell-03-machine-or-account-change", false, "implementar: mudanca de conta");
}

// sell-04 — gratuito → pago sem perder dados; prorratação e imposto ao cêntimo
if (only === "all" || only === "sell-04") {
  check("sell-04-trial-to-paid", false, "implementar: trial -> pago");
}

// sell-05 — reembolso e cancelamento; revogação imediata do acesso no reembolso
if (only === "all" || only === "sell-05") {
  check("sell-05-refund-cancel", false, "implementar: reembolso + cancelamento");
}

// sell-06 — fim do pagamento: tolerância declarada, depois leitura ou exportação;
// os dados nunca ficam reféns
if (only === "all" || only === "sell-06") {
  check("sell-06-end-of-payment", false, "implementar: fim do periodo");
}

console.log(`\nFALHAS: ${fail}`);
process.exit(fail === 0 ? 0 : 1);
