## Why

The `/play/my-draw` page lets users analyse a 15-number selection, but results disappear on navigation or page refresh. Since the dataset is moderate-sized and the app is essentially a personal research tool, storing a permanent local history of analysed draws in the browser's IndexedDB gives users a lightweight, zero-infrastructure record of combinations they have explored — no server round-trips, no auth, no backend schema changes needed.

## What Changes

- A new `useMyDrawStore` composable wraps IndexedDB (via the lightweight `idb` library) to persist, list, and delete My Draw analysis entries.
- The `/play/my-draw` page auto-saves each successful analysis to the store and surfaces a "Recent analyses" panel below the result.
- A new `/play/my-draw/history` sub-page shows the full IndexedDB-backed history with the ability to reload a past entry into the selector.
- A navigation link to the new history sub-page is added to the My Draw page.

## Capabilities

### New Capabilities

- `client-draw-store`: IndexedDB persistence layer for My Draw analysis entries — schema, composable (`useMyDrawStore`), and lifecycle management (open, put, getAll, delete, clear).

### Modified Capabilities

- `research-webapp`: The `/play/my-draw` page gains auto-save on analysis completion and a recent-history panel; a new `/play/my-draw/history` route is added under the play section.

## Impact

- **New dependency**: `idb` npm package (tiny IndexedDB wrapper, ~1 kB gzipped).
- **Affected files**: `client/app/composables/useMyDrawStore.ts` (new), `client/app/pages/play/my-draw.vue` (modified), `client/app/pages/play/my-draw/history.vue` (new), `client/app/types/api.ts` (new local-only type `MyDrawEntry`), `client/package.json` (new dep).
- No service changes. No breaking API changes.
