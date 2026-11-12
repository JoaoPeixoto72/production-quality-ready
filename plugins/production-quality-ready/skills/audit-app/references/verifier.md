# Verifier pass

Run this after the audit, before delivering. Act as a sceptical reviewer: you
validate the evidence, you do not look for new bugs.

**Findings.** Reject any finding without verifiable evidence — it is a
hypothesis, not a finding. Point out missing links in the chain Requirement →
Flow → Layer → Transition → Contract → Cross-cutting → Evidence → Root cause →
Impact → Scope → Fix → Re-test. Point out any mismatch between severity, scope
and impact.

**Matrix.** Change any `✓` without evidence to `?`. Point out any `?` that does
not say what is missing. If a P1/P2 flow has a `?`, or a cross-cutting concern is
left unverified on its relevant axes, declare **“Audit incomplete”**.

Return only the list of corrections.
