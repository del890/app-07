## 1. Service — Vision Prompt Rewrite

- [x] 1.1 Rewrite `service/src/service/prompts/ticket_scan.py`: replace prose grid description with the explicit 5×5 position-to-number mapping table and update instructions to reason by cell coordinate
- [x] 1.2 Update the prompt to reference "Image 1 = blank template, Image 2 = filled ticket" and instruct Claude to diff between the two images

## 2. Service — Reference Image Loading

- [x] 2.1 Add a module-level loader in `service/src/service/api/tickets.py` that reads `_process/lotofacil-bilhete.webp` at import time, base64-encodes it, and stores it in a module variable; log a warning and set the variable to `None` if the file is missing
- [x] 2.2 Update `scan_ticket` to build a two-image-block `content` list when the reference image is available, falling back to the single-block call when it is `None`
- [x] 2.3 Determine the correct `media_type` for the reference `.webp` image and use `image/webp` in its source block

## 3. Client — Capture Resolution & Preprocessing

- [x] 3.1 In `client/app/composables/useTicketScanner.ts`, raise the `MAX` resolution cap from `1280` to `1920`
- [x] 3.2 In `captureFrame`, set `ctx.filter = 'contrast(180%) brightness(110%) saturate(0%)'` on the offscreen canvas context before calling `ctx.drawImage`

## 4. Client — Alignment Guide Overlay

- [x] 4.1 In `client/app/components/TicketScanner.vue`, add an SVG or CSS overlay element (positioned absolute, `pointer-events: none`) centred over the video element with a portrait rectangle (aspect ratio ≈ 1:2.3) and corner markers
- [x] 4.2 Add a text label "Align ticket within the guide" inside or below the overlay frame
- [x] 4.3 Ensure the overlay is only rendered when the camera stream is active (hide it once a frame has been captured and is in review)

## 5. Tests & Verification

- [x] 5.1 Update `service/tests/test_tickets.py`: add a test that verifies the two-image-block path is used when the reference image is available, and the single-image fallback is used when it is `None`
- [ ] 5.2 Manually test the scan flow on mobile: confirm the alignment overlay appears, the capture works, and the results are more accurate than before
