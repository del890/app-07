## ADDED Requirements

### Requirement: Open and version the IndexedDB database on first use
The `useMyDrawStore` composable SHALL open a single IDB database named `lotofacil-app` at version 1, creating an object store named `entries` with an auto-increment integer primary key and a `savedAt` string index (non-unique).

#### Scenario: First-ever open creates the store
- **WHEN** `useMyDrawStore` is called for the first time in a browser with no prior database
- **THEN** IndexedDB reports version 1 and the `entries` object store exists

#### Scenario: Repeated opens reuse the existing connection
- **WHEN** `useMyDrawStore` is called multiple times within the same page session
- **THEN** only one IDB connection is established (module-level singleton promise)

#### Scenario: Open failure degrades gracefully
- **WHEN** `openDB` throws (e.g., private-browsing quota denial)
- **THEN** all store operations become no-ops and `storeAvailable` returns `false`

---

### Requirement: Save a My Draw entry to IndexedDB
The `saveEntry` function SHALL accept a `{ numbers, profile }` payload, attach a `savedAt` ISO timestamp, and persist it to the `entries` store, returning the generated integer `id`.

#### Scenario: Successful save returns an id
- **WHEN** `saveEntry` is called with 15 numbers and a valid `DrawProfileResponse`
- **THEN** a positive integer id is returned and the entry can be retrieved by that id

#### Scenario: Save is a no-op when store unavailable
- **WHEN** `saveEntry` is called after the database failed to open
- **THEN** it resolves to `null` without throwing

---

### Requirement: List all entries in reverse-chronological order
The `listEntries` function SHALL return all `MyDrawEntry` items sorted newest-first by `savedAt`. It MUST NOT require a full-page reload to reflect newly saved entries.

#### Scenario: Returns newest entry first
- **WHEN** two entries are saved at different times and `listEntries` is called
- **THEN** the entry with the later `savedAt` appears first in the array

#### Scenario: Returns empty array when no entries exist
- **WHEN** `listEntries` is called against an empty store
- **THEN** it returns `[]`

---

### Requirement: Delete a single entry by id
The `deleteEntry(id)` function SHALL remove the entry with the given primary key from the store.

#### Scenario: Deleting an existing entry removes it
- **WHEN** `deleteEntry` is called with a valid id
- **THEN** a subsequent `listEntries` call does not include that entry

#### Scenario: Deleting a non-existent id is a no-op
- **WHEN** `deleteEntry` is called with an id that does not exist
- **THEN** no error is thrown

---

### Requirement: Clear all entries
The `clearEntries` function SHALL delete every record from the `entries` store.

#### Scenario: Clear empties the store
- **WHEN** `clearEntries` is called after several entries have been saved
- **THEN** `listEntries` returns `[]`
