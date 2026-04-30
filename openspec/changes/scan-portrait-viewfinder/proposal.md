## Why

The camera viewfinder currently uses a 16:9 landscape container (`aspect-video`), but a Lotofácil ticket is portrait-shaped. The in-overlay guide rectangle is already drawn portrait (`1:2.3`), but it occupies less than half the container width — leaving large black bars on both sides and making it hard to frame the ticket accurately.

## What Changes

- Change the outer camera container aspect ratio from 16:9 (landscape) to 9:16 (portrait) in `TicketScanner.vue` — applies to both the live viewfinder and the captured-image preview introduced by `ticket-scan-preview`.
- Widen the in-overlay guide rectangle so it makes better use of the taller, narrower container.
- Add `aspectRatio: 9/16` to the `getUserMedia` video constraints in `useTicketScanner.ts` so the browser requests a portrait-oriented stream from the camera hardware (best-effort; browsers may ignore this hint).

## Capabilities

### New Capabilities

<!-- No new product capabilities are introduced; this is purely a visual / UX improvement. -->

### Modified Capabilities

- `scan-capture-preview`: The preview image container (introduced by the `ticket-scan-preview` change) must also switch to portrait so the captured still matches the live viewfinder.

## Impact

- **`client/app/components/TicketScanner.vue`**: Update `aspect-video` → `aspect-[9/16]` on the video container and preview image container; adjust guide rectangle width.
- **`client/app/composables/useTicketScanner.ts`**: Add `aspectRatio: 9/16` video constraint hint.
- No service or API changes.
