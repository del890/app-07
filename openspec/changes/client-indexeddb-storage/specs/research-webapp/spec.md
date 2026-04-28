## ADDED Requirements

### Requirement: My Draw page auto-saves each successful analysis
After a successful `fetchProfile` call on `/play/my-draw`, the page SHALL call `saveEntry` from `useMyDrawStore` automatically. The save MUST happen in the background — it MUST NOT block the result render or show a loading state.

#### Scenario: Analysis result triggers auto-save
- **WHEN** the user submits 15 numbers and the service returns a `DrawProfileResponse`
- **THEN** the entry is saved to IndexedDB within the same event loop tick after the result is displayed

#### Scenario: Save failure does not break the result display
- **WHEN** `saveEntry` rejects (e.g., store unavailable)
- **THEN** the analysis result is still displayed normally and the error is silently ignored

---

### Requirement: My Draw page surfaces a recent-history panel
Below the result panel, `/play/my-draw` SHALL render up to 5 most-recently saved entries from IndexedDB. Each entry MUST show the 15 numbers, the `savedAt` timestamp, and a "Load" button.

#### Scenario: Recent entries appear after saving
- **WHEN** a new analysis is saved and the result is shown
- **THEN** the recent-history panel refreshes to include the new entry at the top

#### Scenario: Loading a past entry repopulates the selector
- **WHEN** the user clicks "Load" on a past entry
- **THEN** the `DrawSelector` is populated with that entry's numbers and the previous result is cleared

#### Scenario: Panel is hidden when no entries exist
- **WHEN** no entries have been saved
- **THEN** the recent-history panel is not rendered

---

### Requirement: My Draw history sub-page shows the full IndexedDB history
A new page at `/play/my-draw/history` SHALL list all saved entries from IndexedDB, newest-first. Each entry MUST show the 15 numbers, timestamp, and buttons to "Load" (navigate to `/play/my-draw` with the numbers pre-filled) and "Delete".

#### Scenario: Full history is rendered
- **WHEN** the user navigates to `/play/my-draw/history`
- **THEN** all entries are listed newest-first

#### Scenario: Empty state is shown when no entries exist
- **WHEN** the user navigates to `/play/my-draw/history` with no saved entries
- **THEN** a "No analyses saved yet" message is displayed with a link to `/play/my-draw`

#### Scenario: Deleting an entry removes it immediately
- **WHEN** the user clicks "Delete" on an entry
- **THEN** the entry disappears from the list without a page reload

#### Scenario: Clear all removes every entry
- **WHEN** the user clicks "Clear all" and confirms
- **THEN** all entries are deleted and the empty-state message is shown
