## Context

The service currently ingests `data.json` once at startup via `ingest_from_settings()`, caches the result in a module-level `_cached: DrawHistory | None` protected by a `threading.Lock`, and never re-reads the file. There is no mechanism to fetch new draws from the internet, and the in-memory cache cannot be refreshed without restarting the process.

The client's `/play` section offers three modes (Suggest Next Draw, Scenario Path, History) but no way for a user to enter numbers they are personally considering and immediately see statistical context for those numbers.

This change introduces two orthogonal capabilities that share a dataset dependency:

1. **Automatic dataset sync** — a background task that fetches new Lotofácil draw results from the official Caixa API, appends validated records to `data.json`, and signals a hot-reload of the in-memory history.
2. **User-draw insights** — a new `/play/my-draw` page where the user selects 15 numbers, submits them, and receives a statistical profile (frequency, co-occurrence, structural) plus a dataset-match flag.

## Goals / Non-Goals

**Goals:**
- Fetch new Lotofácil draws automatically from a reliable public source on a configurable interval.
- Update `data.json` atomically and reload the in-memory `DrawHistory` without restarting the service.
- Expose a manual sync trigger (`POST /v1/admin/sync`) and a status endpoint (`GET /v1/admin/sync/status`) for operational control.
- Add a `/play/my-draw` page to the client with a 25-number grid selector enforcing exactly 15 chosen numbers.
- Return per-number frequency, pairwise co-occurrence strength, sum/parity/range structural profile, and a dataset-match flag for the user's chosen draw combination.
- Reuse existing statistics API endpoints as much as possible; introduce a new composite endpoint only if the required data cannot be assembled client-side from existing calls.

**Non-Goals:**
- Real-time push of new draws to connected clients (polling on the client is acceptable).
- Scraped or unofficial data sources — only the official Caixa Econômica Federal Lotofácil API.
- Archival of superseded `data.json` versions beyond a single `.bak` rotation.
- User-specific persistence of entered draws (anonymous session only).
- Any modification to authentication, user accounts, or bet automation.

## Decisions

### Decision 1: Use the official Caixa API for draw sync

**Chosen**: Fetch from `https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil` (the authoritative Caixa Econômica Federal endpoint). It returns structured JSON with draw contest numbers and results, making scraping unnecessary.

**Alternatives considered**:
- Third-party community APIs: fragile, may disappear or introduce errors.
- HTML scraping of the official results page: brittle, breaks on markup changes, and adds `BeautifulSoup` as a heavy dependency.

**Rationale**: Official source + structured JSON = lowest maintenance burden and highest data fidelity.

### Decision 2: APScheduler for the background sync task

**Chosen**: Use `APScheduler` (specifically `AsyncIOScheduler`) to schedule a periodic async sync job that runs inside the existing FastAPI/asyncio event loop.

**Alternatives considered**:
- A plain `asyncio.create_task` loop: simpler but no cron-style scheduling, harder to configure per-environment, and lacks built-in job state tracking.
- A separate cron process / systemd timer: works but adds operational complexity with no benefit at this scale.

**Rationale**: APScheduler integrates with FastAPI's lifespan context manager cleanly, supports a configurable interval via settings, and provides job execution tracking without a full task-queue infrastructure.

### Decision 3: Atomic `data.json` update with write-then-rename

**Chosen**: Write the updated dataset to a temporary file alongside `data.json`, then atomically rename it over the original. A single `.bak` copy of the previous file is kept.

**Alternatives considered**:
- In-place write with a lock file: still has a window where the file is partially written and readable.
- Append-only JSONL side-file: diverges from the existing `data.json` contract, requiring changes across all downstream consumers.

**Rationale**: Write-then-rename is atomic on POSIX filesystems within the same mount point. It preserves the existing `data.json` contract for all downstream consumers.

### Decision 4: Hot-reload via `reload_from_settings()` function

**Chosen**: Expose a new `reload_from_settings()` function in `service.ingestion` that clears `_cached` under the lock and calls `ingest_from_settings()`, replacing the cache atomically. The sync task calls this after a successful file write.

**Alternatives considered**:
- Restart the process: simplest, but loses in-flight requests and adds operational overhead.
- Expose the cache as a dependency-injected object: cleaner long-term, but requires threading dependency injection through all API routes — large scope expansion.

**Rationale**: Minimal diff to the existing cache module. Thread safety is inherited from the existing `_lock`. Downstream consumers calling `get_cached_history()` will transparently receive the new history on the next call.

### Decision 5: New composite stats endpoint for user-draw insights

**Chosen**: Introduce `POST /v1/stats/draw-profile` that accepts a list of 15 numbers and returns frequency, co-occurrence, structural profile, and a dataset-match flag in a single response. Client calls one endpoint instead of orchestrating multiple.

**Alternatives considered**:
- Compose results entirely on the client from existing endpoints: each statistics endpoint returns data for the full dataset; extracting a per-combination profile client-side would require downloading and filtering large payloads in the browser.

**Rationale**: One network round-trip; server can compute the profile in O(N) over the draw history and return only the relevant slice.

### Decision 6: Client-side number grid as a controlled Nuxt component

**Chosen**: A `DrawSelector.vue` component renders a 5×5 grid of number buttons (1–25). Each button toggles selected state. Submit is disabled unless exactly 15 numbers are selected. Built with existing Tailwind CSS; no new UI library dependency.

**Alternatives considered**:
- Free-text input with comma-separated numbers: less discoverable and more error-prone for the exact-15 constraint.
- A reusable number-picker from an external library: adds a dependency for a simple toggle grid.

**Rationale**: Mirrors the physical Lotofácil play slip, is self-validating, and requires only Tailwind (already in the project).

## Risks / Trade-offs

- **[Risk] Caixa API changes or becomes unavailable** → Mitigation: wrap all fetch calls in a try/except; on failure, log the error, skip the sync cycle, and surface the last-sync timestamp via the status endpoint so operators can detect staleness.
- **[Risk] Concurrent sync cycles overlap if one runs longer than the interval** → Mitigation: APScheduler's `max_instances=1` prevents job overlap; the write lock in `reload_from_settings()` prevents partial reads during a reload.
- **[Risk] `data.json` corruption during an abnormal process exit mid-write** → Mitigation: atomic rename ensures the original file is intact until the new file is fully written. The `.bak` provides a single-step rollback.
- **[Risk] Dataset grows large enough that a full in-memory reload becomes slow** → Mitigation: not a concern at current scale (~3,700 draws, < 2 MB) and not expected to change materially in the lifetime of this project.
- **[Risk] The `POST /v1/stats/draw-profile` endpoint is slow to respond under load** → Mitigation: the computation is O(N) over a small in-memory dataset; response time should be < 50 ms. No caching needed at this scale.
- **[Risk] User enters a draw combination with < 15 or > 15 numbers** → Mitigation: the client `DrawSelector` component disables submission unless exactly 15 are selected; the server endpoint validates the payload and returns 422 on violation.

## Migration Plan

1. Add `apscheduler` and `httpx` to `service/pyproject.toml`.
2. Add `sync_interval_minutes: int` and `lotofacil_api_url: str` to `Settings` (with safe defaults).
3. Implement `service.sync` module: fetch, validate, merge, write, reload.
4. Register the scheduler in `lifespan()` in `main.py`.
5. Add `POST /v1/admin/sync` and `GET /v1/admin/sync/status` routes.
6. Add `reload_from_settings()` to `service.ingestion`.
7. Implement `POST /v1/stats/draw-profile` in `service.api.statistics`.
8. Implement `DrawSelector.vue` component in the client.
9. Implement `/play/my-draw` page consuming the new endpoint.
10. Add the "My Draw" link to the `/play` index page.
11. Add tests: sync module unit tests (mocked HTTP), draw-profile endpoint integration test, DrawSelector component interaction test.

**Rollback**: Disable the scheduler in settings (`sync_interval_minutes=0` disables scheduling). The dataset file is unchanged from the pre-change state as long as no sync has run. Reverting the service code restores the original behavior.

## Open Questions

- **Exact Caixa API pagination**: Does the endpoint return all draws in a single response, or does it paginate by contest number? Needs verification before implementing the fetch logic. If paginated, the sync task must iterate from the last known draw ID.
- **Rate limits on the Caixa API**: No documented rate limit found; conservative default of once per hour is suitable until real-world behavior is observed.
- **Admin endpoint auth**: Currently no auth exists on the service. The `POST /v1/admin/sync` manual trigger should be protected (at minimum an internal flag or an API key check), but adding auth infrastructure is out of scope. For now, document that the admin routes are intended for operator use and should not be exposed publicly.
