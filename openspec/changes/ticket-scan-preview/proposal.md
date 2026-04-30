## Why

After capturing a photo, the app immediately sends it to the API without letting the user see what was captured. Blurry, cropped, or poorly-lit photos are silently processed and often return incorrect numbers, wasting a round-trip and confusing users. Adding a captured-image preview step lets users verify the photo quality before committing to the scan.

## What Changes

- After clicking **Capture**, show the captured still image alongside a **Confirm** / **Retake** flow before the image is uploaded to the API.
- Add a visual positioning guide to the scan page with illustrated examples showing correct (and incorrect) ticket orientation, distance, and lighting — so first-time users know how to hold the ticket before they capture.
- The loading and result views remain unchanged.

## Capabilities

### New Capabilities

- `scan-capture-preview`: Preview the captured still image with Confirm / Retake actions before it is uploaded for analysis, giving users a quality-check step between capture and API submission.
- `scan-positioning-guide`: Illustrated tips panel (or modal) on the scan page that shows examples of how to align and position the ticket within the camera guide.

### Modified Capabilities

<!-- No existing spec-level requirements are changing. The TicketScanner component and scan API contract remain the same. -->

## Impact

- **`client/app/components/TicketScanner.vue`**: New `'preview'` view state inserted between `'capture'` and `'loading'`. The captured blob is stored locally; upload is deferred until the user confirms.
- **`client/app/pages/play/scan.vue`**: Minor copy update (instructional paragraph) to point users to the positioning guide.
- **`client/app/composables/useTicketScanner.ts`**: `captureFrame` result held in component state; `uploadImage` is only called after user confirmation.
- No service-side changes; the API contract (`POST /v1/tickets/scan`) is untouched.
