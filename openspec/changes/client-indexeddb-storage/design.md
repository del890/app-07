## Context

The client is a Nuxt 3 / TypeScript / Tailwind app. It currently has no client-side persistence — all history lives on the service (stored predictions) or is lost on navigation. The new `/play/my-draw` page lets users analyse arbitrary 15-number selections, but results are ephemeral. There are no auth/user accounts, so any persistence must be purely local.

## Goals / Non-Goals

**Goals:**
- Persist My Draw analysis entries (input numbers + full `DrawProfileResponse`) forever in the user's browser.
- Let users browse, reload, and delete past entries.
- Work fully offline after the initial page load.
- Zero service changes and no external accounts.

**Non-Goals:**
- Syncing data across devices or browsers.
- Persisting any other data (research charts, prediction history — the service already handles those).
- Implementing a generic key-value storage abstraction for the whole app.
- Using a heavier solution like PouchDB or Dexie.

## Decisions

### D1 — Use `idb` instead of raw `indexedDB` API

**Decision**: Add `idb` (≈1 kB gzipped, zero deps) as a thin promise-based wrapper.

**Alternatives considered**:
- *Raw `indexedDB` API*: Verbose and error-prone (nested callbacks / event listeners). Rejected for maintainability.
- *Dexie*: Full-featured ORM, but ~24 kB gzipped and far more than needed for a single object store.
- *localStorage*: Simple, but synchronous, limited to ~5 MB, and poorly suited for structured JSON blobs.
- *VueUse `useStorage`*: Uses localStorage under the hood — same size limits, not appropriate for potentially large result objects.

**Rationale**: `idb` keeps the implementation close to native IndexedDB semantics while eliminating the callback pyramid. Single-store schema keeps migration complexity near zero.

---

### D2 — Single database `my-draw-store`, single object store `entries`

**Decision**: One IDB database (`lotofacil-app`, version 1) with one object store `entries`, keyed on auto-generated `id` (integer), with a `savedAt` index for chronological listing.

**Schema**:
```ts
interface MyDrawEntry {
  id?: number           // auto-increment primary key
  savedAt: string       // ISO datetime
  numbers: number[]     // the 15 input numbers
  profile: DrawProfileResponse  // full service response
}
```

**Rationale**: The data volume is tiny (users realistically save dozens of entries). A single store with a date index is sufficient. No need for relations or secondary indexes beyond `savedAt`.

---

### D3 — `useMyDrawStore` composable, not a Pinia store

**Decision**: Expose IndexedDB operations through a Nuxt composable (`composables/useMyDrawStore.ts`) that lazily opens the database on first use.

**Alternatives considered**:
- *Pinia store*: Adds a dependency and the in-memory state mirror is unnecessary — the source of truth is IDB, not reactive state.
- *Nuxt plugin*: Lifecycle is trickier; a composable is simpler and testable.

**Rationale**: Consistent with the existing codebase pattern (`useApi`, `useDrawProfile`, etc.). The composable opens the DB once per app session via a module-level promise, so multiple callers share the same connection.

---

### D4 — Auto-save on analysis completion in `my-draw.vue`

**Decision**: After a successful `fetchProfile` call, call `saveEntry` automatically. Do not require the user to click a save button.

**Rationale**: The expectation is that the user always wants to keep a record of what they analysed. Explicit save buttons add friction for no benefit in a personal tool. Duplicate detection (same 15 numbers, most-recent only) is handled by the store via a query before insert.

---

### D5 — `/play/my-draw/history` as a dedicated sub-page

**Decision**: The full history is a separate page (`pages/play/my-draw/history.vue`), not a modal or drawer.

**Rationale**: Keeps `my-draw.vue` focused on the analysis UX. The history page can be deep-linked. A "View history" link on the My Draw page provides discoverability.

## Risks / Trade-offs

- **Browser support**: IndexedDB is supported in all modern browsers. Not available in some unusual environments (e.g., private mode in older Safari versions). Mitigation: degrade gracefully — if `openDB` throws, `useMyDrawStore` returns no-op functions and the app works without persistence; an unobtrusive warning is shown.
- **No cross-device sync**: Entries are local-only. Mitigation: out of scope by design; noted in Non-Goals.
- **Storage quota**: IDB quota is typically 50–100 MB in modern browsers. Mitigation: each entry is roughly 5–10 kB of JSON; 10,000 entries ≈ 100 MB worst case, unlikely in practice. Optionally cap entries at 500 (oldest pruned on overflow).

## Migration Plan

1. Add `idb` to `client/package.json`.
2. Implement `useMyDrawStore` composable.
3. Add `MyDrawEntry` type to `client/app/types/api.ts`.
4. Modify `my-draw.vue` to call `saveEntry` after successful analysis and render the recent-history panel.
5. Create `pages/play/my-draw/history.vue`.
6. No rollback complexity — IDB data is local; removing the code leaves the DB inert.

## Open Questions

- Should duplicate entries (same 15 numbers within the same day) be silently deduplicated or allowed? **Proposed default**: allow duplicates — keep it simple, users can delete manually.
