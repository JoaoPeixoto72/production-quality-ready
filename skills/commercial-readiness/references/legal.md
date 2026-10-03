# legal — commercial-readiness

Checklist for the `legal-clean` check: facts verifiable in the repo. **The
legal conclusion is the seller's**, not this skill's.

## GDPR

- A written privacy policy, reachable in the app and on the site.
- A declared legal basis for each kind of data collected.
- The right to erasure has a documented path.
- No third-party tracker without prior consent.

## CRA (EU Cyber Resilience Act)

- Vulnerabilities reportable to a declared channel (SECURITY.md).
- Security updates separate from feature updates.
- Security support declared for N years after sale.

## EAA (European Accessibility Act)

- WCAG 2.2 AA met (cross-reference `design-pro`).
- An accessible conformance statement.

## EULA

- It exists, written or reviewed by a lawyer.
- Limitation of liability consistent with the price.
- Clear warranty clauses.

## Dependency licences

- FFmpeg and commercial codecs have licences compatible with the sales model.
- Each copyleft dependency (GPL, AGPL) has a carve-out or a planned replacement.
- The release SBOM lists every licence.
