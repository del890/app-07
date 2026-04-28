## 1. Dependency

- [x] 1.1 Add `idb` to `client/package.json` dependencies and run `npm install`

## 2. Types

- [x] 2.1 Add `MyDrawEntry` interface to `client/app/types/api.ts`

## 3. useMyDrawStore Composable

- [x] 3.1 Create `client/app/composables/useMyDrawStore.ts` — open `lotofacil-app` IDB v1 with `entries` object store (auto-increment key, `savedAt` index) using a module-level singleton promise
- [x] 3.2 Implement `saveEntry({ numbers, profile })` — attaches ISO `savedAt`, puts to store, returns generated id (or `null` if store unavailable)
- [x] 3.3 Implement `listEntries()` — returns all entries from the `savedAt` index in reverse order (newest first)
- [x] 3.4 Implement `deleteEntry(id)` — removes the record with the given key; no-op if not found
- [x] 3.5 Implement `clearEntries()` — clears the entire `entries` store
- [x] 3.6 Expose `storeAvailable: boolean` — `false` when `openDB` threw at init time
- [x] 3.7 Wrap `openDB` call in try/catch so that all operations degrade to no-ops on failure (e.g., private-browsing quota denial)

## 4. My Draw Page — Auto-save and Recent History Panel

- [x] 4.1 Import `useMyDrawStore` in `client/app/pages/play/my-draw.vue`
- [x] 4.2 After a successful `fetchProfile`, call `saveEntry` in the background (fire-and-forget, errors swallowed silently) and refresh the recent-entries list
- [x] 4.3 Add a `recentEntries` ref populated by `listEntries()` (sliced to latest 5) that refreshes after each save
- [x] 4.4 Render a "Recent analyses" panel below the result panel showing up to 5 entries (numbers + timestamp + "Load" button); hide the panel entirely when the list is empty
- [x] 4.5 Wire the "Load" button to populate `selectedNumbers` with the entry's numbers and clear the current result

## 5. My Draw History Sub-page

- [x] 5.1 Create `client/app/pages/play/my-draw/history.vue` — on mount, call `listEntries()` and store in a reactive `entries` ref
- [x] 5.2 Render each entry with its 15 numbers, formatted `savedAt` timestamp, a "Load" button (navigates to `/play/my-draw` — pass numbers via `useState` or query), and a "Delete" button
- [x] 5.3 Wire "Delete" to call `deleteEntry(id)` and remove the item from the local `entries` ref immediately (no reload)
- [x] 5.4 Add a "Clear all" button that calls `clearEntries()` after a `window.confirm` prompt, then resets `entries` to `[]`
- [x] 5.5 Show an empty-state message ("No analyses saved yet") with a link to `/play/my-draw` when `entries` is empty

## 6. Navigation

- [x] 6.1 Add a "View history" `NuxtLink` to `/play/my-draw/history` on the `my-draw.vue` page (small link below the recent-history panel or in the page header)
