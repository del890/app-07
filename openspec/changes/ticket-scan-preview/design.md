## Context

The ticket scanner (`TicketScanner.vue` + `useTicketScanner.ts`) currently has three view states: `capture`, `loading`, and `result`. After the user clicks **Capture**, the component immediately stops the camera, compresses the frame with a Canvas filter, and uploads the blob to `POST /v1/tickets/scan` — all without showing the user what was captured.

This creates two UX problems:
1. **No quality gate**: A blurry, dark, or partially-cropped photo is silently submitted and often returns wrong numbers.
2. **No guidance for new users**: The scan page offers only a brief text description. First-time users have no visual reference for how to hold and position the ticket.

Both problems are purely client-side and require no backend changes.

## Goals / Non-Goals

**Goals:**
- Insert a `'preview'` view state between `'capture'` and `'loading'` that displays the captured still image and offers **Confirm** / **Retake** actions.
- Display a positioning-guide panel on the scan page with illustrated examples of good and bad ticket alignment before the user starts capturing.

**Non-Goals:**
- Automated image-quality analysis (blur detection, brightness scoring, etc.) — deferred; the user is the quality judge.
- Modifying the API contract or service layer.
- Changing the result / edit / save flow.

## Decisions

### 1. Store the captured blob as an object URL for preview display

**Choice**: After `captureFrame()` returns a `Blob`, call `URL.createObjectURL(blob)` and store the resulting URL in a `previewUrl` ref alongside the blob. Render it as an `<img :src="previewUrl">` in the new `preview` view. Revoke the URL with `URL.revokeObjectURL()` when leaving the preview view (retake or confirm).

**Alternatives considered**:
- *Convert blob to base64 data-URL*: Works but `btoa` is synchronous and blocks the main thread for large images (up to 1920 px JPEG). Object URLs are zero-copy.
- *Re-draw to a visible canvas element*: More code with no benefit over an `<img>` tag.

**Rationale**: Object URLs are the idiomatic browser API for in-memory blob display — instant, zero-copy, and trivially revoked.

### 2. New `'preview'` view state in the component (not in the composable)

**Choice**: The `'preview'` state lives in `TicketScanner.vue`'s local `view` ref. The composable's `status` remains `'idle'` until `uploadImage` is called (i.e., after the user clicks **Confirm**). The captured `Blob` and its `previewUrl` are stored in component-local refs.

**Alternatives considered**:
- *Add `'preview'` to `ScannerStatus` in the composable*: Couples a UI-only state to the data layer; the composable's consumers (future pages) would need to handle an irrelevant state.
- *Separate preview composable*: Over-engineering for a two-field local state.

**Rationale**: View state that only affects the component's rendering belongs in the component. The composable remains a clean data/network layer.

### 3. Positioning guide as a collapsible tips panel above the viewfinder

**Choice**: Render a static, always-visible tips section on `scan.vue` (above `<TicketScanner>`) with three small annotated illustrations:
1. ✓ Ticket flat, well-lit, fills the guide rectangle.
2. ✗ Ticket at a steep angle / partial.
3. ✗ Finger or shadow obscuring numbers.

Use SVG inline illustrations (no external images) built with simple shapes and text, keeping bundle size negligible.

**Alternatives considered**:
- *Modal / help drawer triggered by an icon*: Adds an interaction step; tips are hidden by default, which is the opposite of what first-time users need.
- *External PNG/JPEG assets*: Requires an image request and adds binary files to the repo.
- *Animated GIF guide*: Distracting and heavier than necessary.

**Rationale**: Inline SVG tips are zero-dependency, accessible, and immediately visible without an interaction step. Three small cards take ≤8 KB uncompressed.

### 4. Preview image shown at the same size as the viewfinder

**Choice**: The `<img>` in the preview view gets the same container constraints as the `<video>` element (`w-full max-w-sm aspect-video object-cover`) so the transition between views is visually seamless.

**Rationale**: Visual continuity reduces user confusion when switching from live video to the still preview.

## Risks / Trade-offs

- **Object URL leak on abrupt navigation**: If the user navigates away while on the preview view, `revokeObjectURL` is never called. Mitigation: call it in `onBeforeUnmount` (already the right place to call `stopCamera`) and in the `handleRetake` / `handleConfirm` paths.
- **Extra tap before upload**: Inserting a confirm step adds friction. Trade-off is intentional — the quality benefit outweighs the extra tap, especially since the current error rate motivates the whole change.
- **SVG illustrations require design effort**: The tips panel contains simplified SVG cards. They are functional but not polished; a designer can refine them later without code changes.

## Open Questions

- Should the positioning guide be dismissible/collapsible to reclaim vertical space for repeat users? Decided to defer — start always-visible; add dismiss toggle in a follow-up if user feedback requests it.
