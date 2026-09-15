# Multimodal Input

Modern products routinely accept camera, voice, scan, image drop, or screen share as first-class inputs — because modern models are natively multimodal. The UX of *providing* that input is a separate craft from the UX of the AI that processes it.

## Checklist

| Item | Guidance |
|---|---|
| Camera entry visible | Camera / scan icon in the input row where it plausibly helps (chat, forms, search). |
| Just-in-time camera permission | Requested when the user taps the camera control, not on launch. Priming screen explains the ask. |
| Voice entry visible | Microphone icon in the input row. Distinct from a "call" or "dictate to system" action. |
| Just-in-time mic permission | Requested when the user taps mic. |
| Live transcript for voice | The user sees words appearing as they speak. Silence detection ends the recording. |
| Voice cancel / retry | Cancel returns to typed input. Retry re-opens mic without re-priming. |
| Push-to-talk vs tap-to-toggle | State is unambiguous — a live "recording" affordance, not just a color change. |
| OCR from photo / scan | Auto-detects document orientation, applies edge detection, offers manual crop before accepting. |
| Scanned text is editable | Extracted text lands in an editable field before submission, not as a locked value. |
| QR / barcode scan | Auto-detects, confirms the target ("Open https://…?") before navigating. |
| Sensitive content re-consent | Health / ID / financial documents show an in-context confirmation of what will be shared and where. |
| On-device vs cloud disclosed | For OCR, transcription, image analysis: the UI states where processing happens. |
| Progress and cancel while processing | Uploads, transcription, OCR: user sees progress and can cancel. |
| Retry with a different mode | If OCR / voice fails, offer typed input as fallback, not a dead end. |
| Multimodal accessibility | Voice input works with dictation off; camera input has a manual-typed alternative; image alt-text prompted where the image is user-shared content. |

## Patterns

**Priming screen for camera / mic.** Before the system dialog, an in-app screen with: what the feature does, where the data goes (on-device or cloud), how to change the choice later. Users who see priming accept permissions at much higher rates.

**OCR review step.** After scan, drop the extracted text into a review screen with editable fields. Even excellent OCR benefits from a review — and the review makes the AI's mistakes forgivable.

**Live transcript.** Show the ASR result as it streams. Cursor / caret at the end. If confidence per token is available, show low-confidence words underlined so the user knows what to correct.

**Silence detection.** End the recording after 1.5–2s of silence for short prompts, longer for narration. Always allow manual stop.

**Screenshot as a prompt.** For AI products that accept a screenshot: paste target visible in the composer (Cmd/Ctrl+V hint), drag-and-drop area highlighted, size limit stated. On mobile, "attach screenshot" from the recent captures.

**Barcode / QR handoff.** Never navigate on scan without a confirmation of the target — QR phishing is a real threat vector.

## Anti-patterns

- Camera permission requested on app launch.
- Voice input with no live transcript — the user has no idea if it's working.
- OCR that commits extracted text directly to submission without a review step.
- QR scan that opens the target URL silently.
- No fallback to typed input when scan / voice fails — traps the user.
- Screenshots or documents shared to a cloud service with no disclosure.
- Recording that continues while the app is backgrounded, with no persistent indicator.

## Platform notes

- **iOS.** Camera and microphone need `NSCameraUsageDescription` / `NSMicrophoneUsageDescription`. The system red dot / green dot indicates active camera / mic. Users see it in Control Center.
- **Android.** Runtime permissions since Android 6. Foreground service required for continued mic access in background. Android 12+ mic and camera indicators in the status bar.
- **Web.** `getUserMedia` requires HTTPS and a user gesture. Chrome / Firefox show a persistent tab indicator.

## Related

- `./safety-privacy.md` — permission priming, denial recovery, data-protection rules.
- `./help-onboarding.md` — first-run guidance for camera / voice.
- `./forms.md` — camera / voice / scan as inputs to form fields.
- `./ai-agent.md` — screenshots and voice as prompts to an agent.
- `./search.md` — voice search entry point.
- `./error-handling.md` — fallback paths when a mode fails.
- `../agent/tool-strategy.md` — which tool to reach for when validating multimodal capture.
