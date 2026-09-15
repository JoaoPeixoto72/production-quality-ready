# Platform Adaptation

Every finding is bound to a platform. iOS ≠ Android ≠ Web.

## Baselines

- **iOS** — Apple Human Interface Guidelines. Typography scale uses iOS body 17pt / caption 12pt. Touch target 44×44pt (HIG). Back gesture: edge swipe. System paste prompt on clipboard read (iOS 16+).
- **Android** — Material 3. Typography scale uses Material's Body/Title/Display roles. Touch target 48×48dp (Material). Back gesture / back button. System toast on clipboard access (Android 12+). Notification channels required.
- **Web** — WCAG 2.2 + Core Web Vitals (LCP 2.5s, INP 200ms, CLS 0.1). No system "back gesture" — browser back must work. No clipboard prompt system-wide; rely on user gesture requirement.

## Rules

- Every finding names the platform if the finding depends on a platform convention.
- Do not write a finding like "the app should follow Material guidance" for an iOS app.
- If a review covers a cross-platform app (iOS + Android + Web), split findings by platform where behavior differs.

## Accessibility floor

WCAG 2.2 applies everywhere. Platform HIGs add extra requirements (Apple's dynamic type support, Android's TalkBack semantics, etc.) but never lower the WCAG floor.
