## 1. Service — Dependencies and Configuration

- [x] 1.1 Add `apscheduler` and `httpx` to `service/pyproject.toml` dependencies
- [x] 1.2 Add `sync_interval_minutes: int` setting to `Settings` in `service/src/service/config.py` (default `60`)
- [x] 1.3 Add `lotofacil_api_url: str` setting to `Settings` (default `https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil`)

## 2. Service — Ingestion Hot-Reload

- [x] 2.1 Add `reload_from_settings()` function to `service/src/service/ingestion/__init__.py` that clears `_cached` under `_lock` and calls `ingest_from_settings()`
- [x] 2.2 Export `reload_from_settings` in `__all__` in `service/src/service/ingestion/__init__.py`
- [x] 2.3 Write unit tests for `reload_from_settings()` covering: reload after file change, thread-safety guarantee, and idempotence

## 3. Service — Dataset Sync Module

- [x] 3.1 Create `service/src/service/sync/` package with `__init__.py`
- [x] 3.2 Implement `service/src/service/sync/fetcher.py`: async function to GET the Caixa API, parse the JSON response, and return a list of raw draw dicts
- [x] 3.3 Implement `service/src/service/sync/merger.py`: validate fetched draws against ingestion schema rules, filter to only draws with IDs newer than the current max, merge, and return the updated draws list
- [x] 3.4 Implement `service/src/service/sync/writer.py`: atomic write-then-rename of `data.json` with `.bak` preservation
- [x] 3.5 Implement `service/src/service/sync/task.py`: orchestrate fetch → validate/merge → write → reload; update last-sync state (timestamp, result, draws-added count)
- [x] 3.6 Write unit tests for the sync module: mocked HTTP success (new draws), mocked no-op (no new draws), mocked HTTP failure (4xx, 5xx, network timeout), and write failure

## 4. Service — Scheduler Registration

- [x] 4.1 Import and initialize `AsyncIOScheduler` from `apscheduler` in `service/src/service/main.py` lifespan
- [x] 4.2 Register the sync task as an interval job when `sync_interval_minutes > 0`
- [x] 4.3 Shut down the scheduler gracefully on lifespan teardown

## 5. Service — Admin Sync API

- [x] 5.1 Create `service/src/service/api/sync.py` with `POST /admin/sync` endpoint that triggers an immediate sync and returns the result
- [x] 5.2 Add `GET /admin/sync/status` to the same file returning `last_sync_at`, `last_sync_result`, `draws_added`, and `total_draws`
- [x] 5.3 Mount the admin router in `service/src/service/api/__init__.py` under `/v1/admin`
- [x] 5.4 Write integration tests for both admin endpoints (success path, error path)

## 6. Service — Draw Profile Endpoint

- [x] 6.1 Add `POST /v1/stats/draw-profile` route to `service/src/service/api/statistics.py` with a Pydantic request body validating exactly 15 unique integers in 1–25
- [x] 6.2 Implement the profile computation: per-number frequency count and rank, pairwise co-occurrence counts for all pairs in the selection, structural metrics (sum, even/odd count, quintile distribution, min-max range)
- [x] 6.3 Implement the dataset-match check: compare the sorted 15-number set against all historical draws and return the matching draw's date and ID (or `null`)
- [x] 6.4 Write integration tests for the draw-profile endpoint covering: valid 15-number input with a dataset match, valid input with no match, validation errors (< 15, > 15, duplicates, out-of-range)

## 7. Client — DrawSelector Component

- [x] 7.1 Create `client/app/components/DrawSelector.vue`: 5×5 grid rendering numbers 1–25 as toggle buttons, tracking selected numbers in a `modelValue` v-model prop
- [x] 7.2 Enforce the exactly-15 constraint in `DrawSelector.vue`: disable selection of additional numbers once 15 are chosen, and expose a computed `isValid` state
- [x] 7.3 Display a selection counter ("X / 15 selected") and a clear-all button in `DrawSelector.vue`

## 8. Client — Draw Profile API Type

- [x] 8.1 Add `DrawProfileRequest` and `DrawProfileResponse` TypeScript types to `client/app/types/api.ts` matching the new service endpoint schema (frequency, co-occurrence, structural, dataset-match)

## 9. Client — useDrawProfile Composable

- [x] 9.1 Create `client/app/composables/useDrawProfile.ts` wrapping `POST /v1/statistics/draw-profile` using the existing `useApi` pattern, with loading/error state management

## 10. Client — My Draw Page

- [x] 10.1 Create `client/app/pages/play/my-draw.vue` with `DrawSelector` for number selection and a submit button
- [x] 10.2 On submit, call `useDrawProfile` and display the result panel: selected numbers highlighted on the grid, per-number frequency indicators, top-5 strongest co-occurring pairs, structural summary (sum, even/odd, quintiles, range)
- [x] 10.3 Show the dataset-match banner ("This draw was played on <date>") when `dataset_match` is non-null; show "This combination has not been drawn before" otherwise
- [x] 10.4 Handle loading and error states in `my-draw.vue` (spinner during fetch, error message on failure)

## 11. Client — Play Index Navigation

- [x] 11.1 Add a "My Draw" `NuxtLink` to `/play/my-draw` in `client/app/pages/play/index.vue` alongside the existing navigation links
