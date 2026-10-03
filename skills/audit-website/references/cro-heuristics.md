# CRO and commercial conversion heuristics (`audit-website`)

Conversion rate optimisation (CRO) judges whether the storefront or landing
page leads the user to complete a goal without friction or deception.

## 1. Conversion principles

### 1.1 Value proposition above the fold
- In under 5 seconds the visitor understands:
  1. What the product or service is.
  2. Who it is for.
  3. Its concrete benefit or difference.
- **Typical defect:** auto-rotating carousels (a distraction that lowers CTR) or poetic, vague titles that do not say what the business does.

### 1.2 Primary call to action (CTA)
- **One evident primary CTA** per screen ("Start free", "Buy now", "Book a demo").
- Higher visual contrast than the page background (WCAG AA).
- The action is in the verb (avoid passive words like "Click here" or "Submit").

### 1.3 Form friction
- Each extra field in a capture form cuts conversion by 3–10%.
- **Required fields:** strictly what the first transaction needs (email and name for a newsletter/lead; never a full address or phone for a simple contact).
- **Usability:**
  - `autocomplete` for browser autofill (`autocomplete="name"`, `autocomplete="email"`);
  - the right mobile keyboard (`type="tel"`, `type="email"`, `inputmode="numeric"`);
  - clear inline validation messages (not a generic "Error").

### 1.4 No manipulative patterns (dark patterns)
- **Pre-ticked checkboxes:** forbidden for marketing consent or add-on subscriptions under the GDPR and the EU Consumer Rights Directive.
- **Hidden costs:** fees, shipping and VAT shown before the final payment step.
- **False urgency:** fake countdowns that restart on every reload.

### 1.5 Social proof and trust
- Verifiable signs of authority:
  - testimonials with real identification, client logos or certifications;
  - customer support details (contact, email, company tax ID in the footer);
  - security seals and recognised payment methods at checkout.
