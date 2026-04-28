## 1. Service — Ticket OCR API

- [x] 1.1 Create `service/src/service/prompts/ticket_scan.py` with the structured Claude Vision prompt constant
- [x] 1.2 Create `service/src/service/api/tickets.py` — FastAPI router with `POST /v1/tickets/scan`, `UploadFile` parameter, 4 MB size guard, JPEG/PNG content-type validation
- [x] 1.3 Implement the scan handler: encode uploaded image as base64, call Anthropic vision API using the prompt from 1.1, parse the JSON response into `ScannedTicket`
- [x] 1.4 Add `ScannedTicket` Pydantic model (`{"games": list[list[int]]}`) to `service/src/service/models/`
- [x] 1.5 Add error handling: return HTTP 422 with `unreadable_ticket` code on JSON parse failure, `no_marks_detected` when `games` is empty
- [x] 1.6 Register the tickets router in `service/src/service/main.py` and apply the existing rate-limit dependency
- [x] 1.7 Write unit tests in `service/tests/test_tickets.py` — mock Anthropic client, cover: valid scan, oversized image (413), invalid type (422), malformed model response (422), empty games (422), rate limit (429)

## 2. Client — `useTicketScanner` Composable

- [x] 2.1 Create `client/app/composables/useTicketScanner.ts` — export `startCamera()`, `stopCamera()`, `captureFrame()`, `uploadImage(blob)`, and reactive state (`stream`, `status`, `error`, `result`)
- [x] 2.2 Implement `startCamera()`: call `navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })` and expose the stream; handle `NotAllowedError` by setting a `permissionDenied` flag
- [x] 2.3 Implement `captureFrame()`: draw the current video frame to an offscreen canvas, resize to max 1280 px longest side, export as JPEG blob at quality 0.85
- [x] 2.4 Implement `uploadImage(blob)`: POST to `/api/v1/tickets/scan` as `multipart/form-data`, update `status` to `loading`/`success`/`error` accordingly
- [x] 2.5 Implement `stopCamera()`: iterate `stream.getTracks()` and call `.stop()` on each; call this in `onUnmounted`

## 3. Client — `TicketScanner.vue` Component

- [x] 3.1 Create `client/app/components/TicketScanner.vue` with three internal view states: `capture`, `loading`, `result`
- [x] 3.2 **Capture view**: render `<video>` bound to the camera stream with a "Capture" button; show file-input fallback when `permissionDenied` is true
- [x] 3.3 **Loading view**: display a spinner and "Analysing ticket…" label; disable all interactive controls
- [x] 3.4 **Result view**: for each game set in `result.games`, render a 5-column number grid (numbers 01–25); marked cells have a distinct highlight style; each cell is clickable to toggle
- [x] 3.5 Add "Save" button (emits `confirm` event with the first game's numbers) and "Discard" button (resets to capture view) to the result view
- [x] 3.6 Add "Retake" button on the result view that stops the upload state and resumes the live viewfinder
- [x] 3.7 Call `useTicketScanner.stopCamera()` in `onUnmounted` to release the camera on component teardown

## 4. Client — `/play/scan` Page

- [x] 4.1 Create `client/app/pages/play/scan.vue` — render `TicketScanner.vue`, handle the `confirm` event by calling `useMyDrawStore.put()` with the received numbers, then navigate to `/play/my-draw`
- [x] 4.2 Add page title / `<Head>` meta: "Scan ticket – Lotofácil"

## 5. Client — Navigation Integration

- [x] 5.1 Add an "Import from scan" button/link to `client/app/pages/play/my-draw.vue` that navigates to `/play/scan`

## 6. Client — Types

- [x] 6.1 Add `ScannedTicket` TypeScript interface to `client/app/types/api.ts`: `{ games: number[][] }`

## 7. Verification

- [x] 7.1 Run `uv run pytest service/tests/test_tickets.py` — all tests pass
- [x] 7.2 Run `npm run lint` in `client/` — no new errors
- [ ] 7.3 Manual smoke test: open `/play/scan`, scan the sample ticket image (`_process/lotofacil-filled.png`), verify detected numbers, confirm save, check My Draw page shows the numbers
