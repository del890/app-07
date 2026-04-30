## 1. Camera Stream

- [x] 1.1 In `useTicketScanner.ts`, add `aspectRatio: 9/16` as an `ideal` constraint inside the `getUserMedia` video options

## 2. Viewfinder Container

- [x] 2.1 In `TicketScanner.vue`, change the live camera container class from `aspect-video` to `aspect-[9/16]`
- [x] 2.2 Update the preview image container (added by `ticket-scan-preview`) from `aspect-video` to `aspect-[9/16]`
- [x] 2.3 In the guide overlay, increase the guide rectangle width from `52%` to `75%`

## 3. Verification

- [x] 3.1 Run `npm test` and confirm all tests pass
- [ ] 3.2 Manually verify the viewfinder is portrait-shaped on the scan page
- [ ] 3.3 Manually verify the ticket guide rectangle is visually centred and fills most of the portrait container
- [ ] 3.4 Manually verify the captured-image preview is also portrait-shaped after clicking Capture
