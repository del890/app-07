## Context

The app currently has no path from a physical ticket to digital numbers. Users must enter each number by hand in the My Draw page. The project already has an Anthropic client running in the service and an IndexedDB store (`useMyDrawStore`) on the client. The ticket format is well-defined: 1–3 game grids, each a 5×5 matrix of numbers 01–25, with marked cells identified by a heavy ink stroke or cross.

## Goals / Non-Goals

**Goals:**
- Provide a camera-based capture flow (live viewfinder + still capture) on both mobile and desktop.
- Detect marked numbers on up to 3 game grids per ticket using Claude's vision capability.
- Return a structured result the client can review, optionally edit, and save into the My Draw store.
- Keep the feature entirely within the existing service and client stacks (no new infra).

**Non-Goals:**
- Offline / on-device OCR (accuracy is too low for handwritten marks without significant tuning).
- Batch scanning of multiple tickets in one session.
- Detecting ticket metadata (contest number, bet type, Surpresinha flags, etc.).
- Automatic submission — the user always confirms before saving.

## Decisions

### 1. Vision backend: Claude Vision API via the service

**Choice**: Route the image through `POST /v1/tickets/scan` in the FastAPI service, which calls Claude with a vision-capable model.

**Alternatives considered**:
- *Browser-based OCR (Tesseract.js)*: No server round-trip, but Tesseract is designed for printed text, not hand-filled grids. Detecting "which cells are marked" requires custom image segmentation not present in the library.
- *Dedicated CV library (OpenCV in service)*: Accurate but requires significant custom grid-detection logic and adds a heavy C-extension dependency.

**Rationale**: Claude Vision handles varied lighting, skew, and hand-mark styles without custom training. The Anthropic client is already wired up; adding a vision call is a minimal incremental change.

### 2. Image transmission: multipart/form-data upload

**Choice**: Client `POST`s the captured JPEG as multipart/form-data (field name `image`). Max accepted size: 4 MB.

**Alternatives considered**:
- *Base64 JSON body*: Easier to type but inflates payload by ~33 % and complicates streaming use in future.
- *Signed upload URL*: Unnecessary complexity for a single-user tool.

**Rationale**: Multipart is the standard HTTP idiom for file upload, keeps the JSON payload clean, and is trivial to handle with FastAPI's `UploadFile`.

### 3. Camera capture: `getUserMedia` with `<input capture>` fallback

**Choice**: Primary path uses the browser's `getUserMedia` API to show a live viewfinder inside `TicketScanner.vue`. A hidden `<input type="file" accept="image/*" capture="environment">` serves as fallback for browsers that block `getUserMedia` (e.g. insecure context) or when the user declines camera permission.

**Rationale**: `getUserMedia` gives a smooth live-preview experience. The `<input capture>` fallback costs nothing and covers the permission-denied case without error screens.

### 4. Client image compression before upload

**Choice**: After capture, the client draws the frame to an offscreen `<canvas>` and exports it as JPEG at quality 0.85, capped at 1280 px on the longest side. This keeps the upload well under the 4 MB limit even on high-resolution phone cameras.

**Rationale**: Compression happens in the browser with zero extra dependencies (canvas API is universally available). The quality level is high enough for Claude to read grid marks reliably.

### 5. Result flow: review → optional edit → save to My Draw store

**Choice**: After a successful scan the `/play/scan` page shows each detected game set (numbers displayed as a mini grid with marks highlighted). The user can toggle individual numbers on/off before confirming. On confirm, the first game set is passed to `useMyDrawStore.put()` and the user is navigated to `/play/my-draw`.

**Rationale**: Auto-save without review risks silently persisting wrong data (camera blur, ambiguous marks). A one-step confirmation screen is lightweight and eliminates that risk.

### 6. Prompt design for Claude Vision

The service sends a single `user` message with the image block followed by a structured text prompt:

```
You are reading a Lotofácil lottery ticket.
The ticket has up to 3 game grids. Each grid contains the numbers 01–25 arranged in a 5×5 matrix.
Marked numbers are identified by a heavy pen stroke or cross through the cell.

Return ONLY valid JSON in this exact shape — no prose:
{"games": [[<marked numbers for game 1>], [<marked numbers for game 2>], ...]}

Numbers must be integers 1–25. Include only marked numbers. Omit empty grids.
```

**Rationale**: Strict output format avoids any post-processing ambiguity. Instructing the model to return only JSON (no prose) eliminates wrapping text. Tested against sample tickets in `_process/`.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Claude misreads ambiguous marks (light strokes, corrections) | Confirmation/edit step lets users fix errors before saving |
| `getUserMedia` not available on HTTP (non-localhost) dev origins | Development server runs on `localhost`; production must be served over HTTPS |
| Large images slow upload on mobile networks | Client-side resize/compress before upload (see Decision 4) |
| Rate-limit abuse of the scan endpoint (each call costs LLM tokens) | Apply the existing `PREDICTIONS_RATE_LIMIT_PER_MINUTE` limiter to the `/v1/tickets/*` router |
| Model changes rendering the fixed prompt unreliable | Prompt is isolated in `service/src/service/prompts/ticket_scan.py`; easy to update |

## Migration Plan

1. Add the new `/v1/tickets/scan` endpoint (additive — no existing routes change).
2. Deploy updated service.
3. Deploy updated client with the new `/play/scan` page and navigation link.
4. No data migrations required.

**Rollback**: Remove the `/play/scan` page entry from the Nuxt router and unregister the FastAPI router — no persistent data is written server-side.

## Open Questions

- Should scanned numbers from multiple game grids be saved as separate My Draw entries, or should only the first grid be used? *(Current design: first grid only, matching the single-selection model of My Draw. Revisit if multi-game support is added.)*
