## Why

Players fill out physical Lotofácil tickets by hand and currently have no fast way to get those numbers into the app — they must type each number manually. A camera-based ticket scanner lets users point their phone or webcam at the ticket, instantly reading all marked numbers into the app, eliminating transcription errors and friction.

## What Changes

- **New `/play/scan` page**: Camera capture screen with live viewfinder, a "Capture" button, and a confirmation/edit step before saving.
- **New `TicketScanner.vue` component**: Manages `getUserMedia` camera stream, still-frame capture, and image upload.
- **New service endpoint `POST /v1/tickets/scan`**: Accepts a JPEG/PNG image (base64 or multipart), uses Claude's vision capability to detect which numbers are marked in each game grid, and returns up to 3 sets of numbers.
- **`useTicketScanner` composable**: Wraps camera lifecycle, image capture, and the HTTP call to the scan endpoint.
- The scanned numbers feed directly into the existing My Draw flow (pre-populating `useMyDrawStore`).

## Capabilities

### New Capabilities

- `ticket-scanner-ui`: Client-side camera capture UI — `TicketScanner.vue` component, `/play/scan` page, and `useTicketScanner` composable. Handles camera permission, live preview, capture, and confirmation.
- `ticket-ocr-api`: Service endpoint `POST /v1/tickets/scan` that receives a ticket image and returns structured marked-number sets by using Claude's vision API.

### Modified Capabilities

- `research-webapp`: A new `/play/scan` route is added to the play section; the My Draw page gains an "Import from scan" shortcut that navigates to `/play/scan`.

## Impact

- **New files**: `client/app/components/TicketScanner.vue`, `client/app/composables/useTicketScanner.ts`, `client/app/pages/play/scan.vue`
- **Modified files**: `client/app/pages/play/my-draw.vue` (add scan shortcut), `client/app/types/api.ts` (new `ScannedTicket` type), `service/src/service/api/` (new scan router), `service/src/service/main.py` (register router)
- **No new npm dependencies** (WebRTC via native browser APIs; image handling via `canvas` API already available).
- **No new Python dependencies** (Anthropic client already present; image data sent as base64 within existing Claude message format).
