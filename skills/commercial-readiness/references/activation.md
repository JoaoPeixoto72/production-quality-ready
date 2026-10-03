# activation — commercial-readiness

Ruler for the checks `sell-01-activation` to `sell-06-end-of-payment`.

## sell-01-activation (happy path and errors)

- Happy path: buy → receive key → activate → app activated.
- Error 1: invalid key — a clear message that does not reveal whether the key exists (no oracle).
- Error 2: key already used on another device — clear instructions to deactivate the old one.

## sell-02-activation-offline

A declared grace period (e.g. 30 days without reaching the server) and a
declared revalidation (what happens on day 31 offline: block, warning, or
fall back to trial?).

## sell-03-machine-change

- Can the user deactivate the old machine from the new one?
- From the web (if the licence server has a UI)?
- Reactivate on a new machine without contacting support?

## sell-04-trial-to-paid

- Do trial files open in the paid version without manual conversion?
- Is the trial counter honest (not reset by reinstalling)?

## sell-05-refund-cancel

- Refund has a page, a form, a declared SLA.
- Cancelling needs no human contact.
- The user's files stay accessible after cancelling (see sell-06).

## sell-06-end-of-payment

When payment stops, the user **does not lose access to the files they
created**. Two accepted options:

1. The app becomes read-only (opens, shows, exports; does not edit).
2. A guaranteed export to an open format on cancelling.

Locked data = `BLOCKER`.
