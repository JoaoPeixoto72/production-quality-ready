# Safety and Privacy

Privacy is a right. Security is a promise. Both must be designed explicitly — users should not have to choose between convenience and protection.

## Checklist

| Item | Guidance |
|---|---|
| Biometric authentication | Face ID / fingerprint available for re-entry and sensitive actions. |
| Permission on use | Prompt at the moment the feature that needs it is invoked. Never on launch. |
| Location permission | "While Using" first. "Always" only when strictly necessary and explained. |
| Permission priming | Pre-permission screen explains the ask before the system dialog. |
| Data protection | Encryption at rest and in transit. Sensitive fields masked. |
| Multi-device management | User views signed-in devices and revokes access remotely from Settings. |
| Two-factor authentication | TOTP with SMS as fallback and backup codes for recovery. |
| Passkeys where supported | FIDO2 passkeys as the primary option. |
| Privacy policy accessible | Link from Settings > About and during account creation. |
| GDPR: right to access | "Download your data" in Account settings. |
| GDPR: right to erasure | "Delete account and all data". |
| GDPR: right to portability | Export as JSON or CSV. |
| Consent | Opt-in for marketing, separate from transactional. No pre-ticked boxes. |
| Data minimization | Collect only what you use. Delete what you no longer need. |
| Privacy by default | Most private settings are the defaults. |
| Analytics disclosure | Analytics providers listed in the privacy policy. |
| Recovery path when denied | If a permission is denied, show a message + deep-link to Settings. |

## Authentication patterns

| Method | Notes |
|---|---|
| Passkeys (FIDO2) | Best UX + strongest security. Phishing-resistant. Primary option where supported. |
| TOTP 2FA | Authenticator apps (Google Authenticator, Authy). 6-digit rotating codes. |
| SMS OTP | Vulnerable to SIM swap. Fallback only. |
| Magic links | Single-use, expire in 15 minutes. |
| Biometrics | Local only. Biometric data never leaves the device. |

## GDPR UX map

| Requirement | UX implementation |
|---|---|
| Right to access | "Download your data" |
| Right to erasure | "Delete account and all data" flow with confirmation |
| Right to portability | JSON / CSV export |
| Consent | Separate marketing opt-in |
| Data minimization | Collect only what's used |
| Privacy by default | Most-private = default |

## Anti-patterns

- Requesting all permissions on launch.
- No path to enable a denied permission other than uninstall + reinstall.
- Pre-ticked "consent" boxes.
- "Delete account" requires emailing support.
- Analytics providers omitted from the privacy policy.

## Related

- `./user-account.md` — login, session, account deletion.
- `./notifications.md` — permission timing and per-type granularity.
- `./settings.md` — where privacy controls live.
- `./accessibility.md` — accessible authentication (WCAG 3.3.8).
- `./consent-and-autonomy.md` — consent flows when an *agent* takes actions on the user's behalf.
