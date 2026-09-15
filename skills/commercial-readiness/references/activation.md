# activation — commercial-readiness

Régua para os checks `sell-01-activation` a `sell-06-end-of-payment`.

## sell-01-activation (feliz e erros)

- Fluxo feliz: comprar → receber chave → activar → app fica activada.
- Erro 1: chave inválida — mensagem clara, sem revelar se a chave existe (evitar oráculo).
- Erro 2: chave já usada noutro dispositivo — instrução clara de como desactivar o anterior.

## sell-02-activation-offline

Grace period declarado (ex: 30 dias sem contactar servidor). Revalidação
declarada (o que acontece no dia 31 sem rede: bloqueio, warning, ou
degradação para trial?).

## sell-03-machine-change

- O utilizador consegue desactivar máquina antiga a partir da nova?
- Consegue desactivar a partir da web (se o servidor de licenças tem UI)?
- Consegue reactivar em máquina nova sem contactar suporte?

## sell-04-trial-to-paid

- Ficheiros do trial abrem na versão paga sem conversão manual?
- Contador de trial é honesto (não reinicia com reinstalação)?

## sell-05-refund-cancel

- Refund tem página, formulário, SLA declarado.
- Cancelamento não exige contacto humano.
- Ficheiros do utilizador continuam acessíveis após cancelamento (ver sell-06).

## sell-06-end-of-payment

Quando o pagamento pára, o utilizador **não perde acesso aos ficheiros que
criou**. Duas opções aceites:

1. App fica read-only (abre, mostra, exporta; não edita).
2. Export garantido para formato aberto ao cancelar.

Dados presos = `BLOCKER`.
