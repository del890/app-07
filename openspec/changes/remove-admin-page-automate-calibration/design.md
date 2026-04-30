## Context

The service currently requires a human to visit `/admin` and click "Executar Calibração" before the Play mode becomes usable. The service already runs data ingestion and dataset sync automatically on startup; calibration is the only step that was left manual. The Admin page exists purely to bridge that gap.

The service uses APScheduler for periodic dataset syncs (`sync_interval_minutes`). The `run_sync` coroutine handles the full sync lifecycle. The `run_calibration` function in `service.engine` is synchronous and CPU-bound (scikit-learn model fitting). The `POST /v1/calibrate` API endpoint already wraps it correctly.

## Goals / Non-Goals

**Goals:**
- Run calibration automatically on service startup (after ingestion) if the engine is stale.
- Trigger re-calibration automatically after each successful dataset sync.
- Remove the Admin page and its nav link from the client entirely.

**Non-Goals:**
- Remove the `POST /v1/calibrate` or `GET /v1/calibrate/status` API endpoints (kept for CI and manual debugging).
- Add authentication or access control to any endpoint.
- Change calibration logic, staleness threshold, or eval metrics.

## Decisions

### 1 — Run calibration in the startup lifespan, not as a separate endpoint call

**Decision**: Add a calibration step to `main.py`'s `lifespan` context manager, immediately after `ingest_from_settings(settings)`.

**Rationale**: The lifespan already sequences startup steps. Running calibration there guarantees it completes before the app begins accepting requests, so the readiness check passes from the first request. Running it elsewhere (e.g. background task, first-request hook) would leave a window where the service reports "not ready".

**Alternative considered**: Start a background task and let the first `/v1/ready` poll wait. Rejected — adds complexity and the startup time impact is the same either way.

### 2 — Re-calibrate after each successful sync in `run_sync`

**Decision**: At the end of `run_sync`, after `reload_from_settings()` succeeds and new draws were added (`draws_added > 0`), call `run_calibration(get_cached_history())`.

**Rationale**: Calibration is only meaningful if the dataset changed. Keeping it inside `run_sync` keeps all post-sync side-effects in one place and avoids scheduler coupling.

**Alternative considered**: A separate scheduled calibration job (e.g., every 24 h). Rejected — the dataset is the only input to calibration, so re-running on every sync is both sufficient and simpler.

### 3 — run_calibration is synchronous; wrap it with asyncio.to_thread

**Decision**: Both in `lifespan` and in `run_sync` (which is `async`), call calibration as `await asyncio.to_thread(run_calibration, history)`.

**Rationale**: `run_calibration` is CPU-bound (model fitting). Running it on the event-loop thread would block all async I/O for several seconds. `asyncio.to_thread` moves it to the thread pool without requiring new dependencies.

**Exception in lifespan**: The lifespan context manager blocks startup anyway, so wrapping with `asyncio.to_thread` is not strictly required there — but it's consistent and prevents any event-loop starve during the startup window.

### 4 — Delete the Admin page completely; keep the API endpoints

**Decision**: Delete `client/app/pages/admin/index.vue` and remove the `/admin` nav link from `layouts/default.vue`. The `POST /v1/calibrate` and `GET /v1/calibrate/status` endpoints are untouched.

**Rationale**: The page only existed as a manual trigger. Keeping the API endpoints preserves debuggability and allows smoke tests to verify calibration status after deployment.

## Risks / Trade-offs

- **Startup time increase**: Calibration adds ~5–15 s to cold startup depending on dataset size. Acceptable for a dev/research app; Render.com free tier has a generous startup timeout.  
  → Mitigation: Log start/end timestamps so slow startups are visible in logs.

- **If ingestion fails, calibration is skipped**: `get_cached_history()` returns `None` when ingestion hasn't run. Calibration must guard against this (it already does — the `/v1/calibrate` endpoint raises `503` if history is `None`; the same guard should be applied to the direct call).  
  → Mitigation: Check `get_cached_history() is not None` before calling `run_calibration` in both lifespan and sync task.

- **Sync re-calibration on no-op syncs**: If a sync run adds 0 draws we skip re-calibration (already covered by `draws_added > 0` guard), so there is no unnecessary work.

## Migration Plan

1. Deploy updated service — calibration now runs on startup.
2. Delete the Admin page from the client.
3. Verify `/v1/ready` returns 200 after deployment (calibration check passes).
4. No rollback complexity — the API endpoints still exist if manual re-calibration is ever needed via `curl`.
