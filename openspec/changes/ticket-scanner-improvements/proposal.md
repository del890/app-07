## Why

The ticket scanner fails to reliably detect marked numbers from smartphone photos because the current vision prompt lacks knowledge of the ticket's fixed grid layout, and heavy ink marks completely obscure the printed numbers. Since the Lotofácil ticket structure is always the same (fixed positions, fixed number arrangement), the system can be significantly improved by encoding that structural knowledge into the prompt and improving the captured image before it reaches the model.

## What Changes

- **Vision prompt rewrite**: Replace the generic description with an exact, position-aware layout map that tells Claude where each number lives in the grid (e.g. "row 3, column 2 is always number 17"). Because heavy ink covers the printed digits, Claude must detect mark presence by cell position, not by reading the obscured digit.
- **Reference image in the vision call**: Send the blank reference ticket (`_process/lotofacil-bilhete.webp`) alongside the user's photo so Claude can perform a visual diff (marked cell vs. clean cell) rather than relying solely on the filled photo.
- **Client image preprocessing**: Before uploading, apply canvas-based contrast enhancement and grayscale conversion so ink marks are more visually distinct from the paper background, improving model accuracy.
- **Camera capture UI overlay**: Add a rectangular guide overlay in the `TicketScanner.vue` viewfinder to help the user align the ticket, fill the frame, and hold it straight.
- **Higher capture resolution**: Increase the client-side capture resolution cap from 1280 px to 1920 px to preserve more detail in the grid cells.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `ticket-ocr-api`: Vision prompt rewritten with exact fixed-layout position map; reference blank ticket image added to the Claude call as a second image block.
- `ticket-scanner-ui`: Camera viewfinder gains an alignment guide overlay; captured image goes through a contrast-boost preprocessing step before upload; capture resolution cap raised.

## Impact

- **Service**: `service/src/service/prompts/ticket_scan.py` (prompt rewrite), `service/src/service/api/tickets.py` (encode and attach reference image to Claude call).
- **Client**: `client/app/composables/useTicketScanner.ts` (preprocessing + resolution), `client/app/components/TicketScanner.vue` (alignment overlay).
- **Assets**: `_process/lotofacil-bilhete.webp` read at service startup and cached as base64.
- **No new dependencies**, no API contract changes, no breaking changes.
