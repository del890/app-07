## 1. Capture Preview — TicketScanner component

- [x] 1.1 Add `previewUrl` and `capturedBlob` refs to `TicketScanner.vue` to store the captured image data
- [x] 1.2 Extend the local `ViewState` type with a `'preview'` value
- [x] 1.3 Update `handleCapture` to store the blob and its object URL, stop the camera, then transition to `'preview'` instead of immediately calling `uploadImage`
- [x] 1.4 Add a `handleConfirmPreview` function that calls `uploadImage(capturedBlob)` and revokes the object URL
- [x] 1.5 Add a `handleRetakeFromPreview` function that revokes the object URL, clears the refs, and calls `startCamera()` then transitions back to `'capture'`
- [x] 1.6 Call `URL.revokeObjectURL` in `onBeforeUnmount` if `previewUrl` is set, to avoid memory leaks on navigation

## 2. Capture Preview — Template

- [x] 2.1 Add a `<template v-else-if="view === 'preview'">` block to `TicketScanner.vue`
- [x] 2.2 Render the captured still image using `<img :src="previewUrl" />` inside the same `max-w-sm aspect-video` container used for the `<video>` element
- [x] 2.3 Add a **Confirm** button that calls `handleConfirmPreview`
- [x] 2.4 Add a **Retake** button that calls `handleRetakeFromPreview`

## 3. Positioning Guide — scan.vue

- [x] 3.1 Add a positioning guide section above `<TicketScanner>` in `scan.vue`
- [x] 3.2 Create an inline SVG card illustrating the correct alignment (ticket flat, centred in guide, well-lit)
- [x] 3.3 Create an inline SVG card illustrating an incorrect alignment (steep angle or partial crop), marked with a red ✗ indicator
- [x] 3.4 Create an inline SVG card illustrating another common mistake (finger or shadow covering numbers), marked with a red ✗ indicator
- [x] 3.5 Style the guide as a horizontal row of cards (or compact vertical stack on narrow screens) that sits above the viewfinder and does not overlap it

## 4. Verification

- [ ] 4.1 Manually test the full capture → preview → confirm → result flow on desktop browser
- [ ] 4.2 Manually test the Retake path (preview → camera restarts correctly)
- [ ] 4.3 Verify that navigating away from the scan page while on the preview view does not leave a dangling object URL (check memory via browser DevTools)
- [ ] 4.4 Verify the positioning guide cards are visible on the scan page before camera starts
- [x] 4.5 Run `npm run lint` and `npm run test` in the `client/` directory and confirm no new errors
