## ADDED Requirements

### Requirement: Fetch latest draws from the official Caixa API on a configurable schedule
The service SHALL periodically fetch the latest Lotofácil draw results from the configured `LOTOFACIL_API_URL` (defaulting to the official Caixa Econômica Federal endpoint). The interval SHALL be configurable via the `SYNC_INTERVAL_MINUTES` setting. A value of `0` for the interval MUST disable automatic scheduling entirely.

#### Scenario: New draws are fetched and persisted automatically
- **WHEN** the sync interval elapses and new draws are available at the remote source
- **THEN** the service validates and merges the new draws into `data.json` and hot-reloads the in-memory dataset

#### Scenario: No-op when the dataset is already up to date
- **WHEN** the sync runs and the remote source reports no contest IDs newer than the latest locally stored draw
- **THEN** `data.json` is not written and the in-memory history is not reloaded

#### Scenario: Scheduling is disabled via setting
- **WHEN** `SYNC_INTERVAL_MINUTES` is set to `0`
- **THEN** no background job is registered at startup and automatic sync never runs

### Requirement: Validate fetched draws before persisting
The sync layer MUST validate every draw fetched from the remote source against the same schema rules used for `data.json` ingestion (DD-MM-YYYY date, exactly 15 numbers per draw, each number an integer in 1–25, no duplicates). Invalid records MUST be rejected and logged; they MUST NOT be appended to `data.json`.

#### Scenario: Malformed remote record is rejected
- **WHEN** the remote API returns a draw with an out-of-range number or incorrect count
- **THEN** that record is logged as invalid, skipped, and `data.json` is not updated with it

#### Scenario: Valid new records pass validation
- **WHEN** the remote API returns well-formed draws with draw IDs not present in the current dataset
- **THEN** those records are appended to the dataset and pass all schema checks

### Requirement: Write `data.json` atomically
When new draws are persisted, the service MUST write the updated dataset to a temporary file and rename it over `data.json` atomically. A backup of the previous `data.json` MUST be preserved as `data.json.bak` immediately before the rename.

#### Scenario: Atomic write succeeds
- **WHEN** the sync task writes new draws
- **THEN** `data.json` is replaced atomically, `data.json.bak` contains the previous version, and no partial file is observable during the write

#### Scenario: Write failure leaves original intact
- **WHEN** the temporary file write fails (e.g., disk full)
- **THEN** `data.json` remains unchanged and the error is logged

### Requirement: Hot-reload the in-memory dataset after sync
After a successful atomic write, the sync task MUST trigger a hot-reload of the `DrawHistory` cache without restarting the service process. Subsequent API requests MUST observe the updated dataset.

#### Scenario: Downstream responds with fresh data after sync
- **WHEN** a sync completes and a new draw was added
- **THEN** the next call to `get_cached_history()` returns a `DrawHistory` that includes the new draw

#### Scenario: Reload is thread-safe
- **WHEN** a hot-reload occurs concurrently with an in-flight API request reading the history
- **THEN** the in-flight request either completes on the old history or the new history — it never observes a partially-updated state

### Requirement: Expose a manual sync trigger and status endpoint
The service SHALL expose `POST /v1/admin/sync` to trigger a sync immediately and `GET /v1/admin/sync/status` to report the last sync attempt time, result, and current dataset row count.

#### Scenario: Manual sync trigger runs sync immediately
- **WHEN** an operator calls `POST /v1/admin/sync`
- **THEN** a sync job runs synchronously (or is enqueued with a short timeout) and the response reports whether new draws were added

#### Scenario: Status endpoint reports last sync outcome
- **WHEN** an operator calls `GET /v1/admin/sync/status`
- **THEN** the response includes `last_sync_at`, `last_sync_result` (success / no-op / error), `draws_added`, and `total_draws`

### Requirement: Graceful degradation on remote source failure
If the external Caixa API is unreachable or returns an unexpected response, the sync task MUST log the failure, skip the cycle, and not modify `data.json` or the in-memory cache. The service MUST remain fully operational with the existing dataset.

#### Scenario: Remote API unreachable
- **WHEN** the sync task cannot reach the remote endpoint (timeout or DNS failure)
- **THEN** an error is logged with the failure reason, the sync cycle is skipped, and existing API endpoints continue to serve the current dataset

#### Scenario: Remote API returns an HTTP error
- **WHEN** the remote endpoint responds with a 4xx or 5xx status code
- **THEN** the sync cycle is aborted, the error status code is logged, and `data.json` is not modified
