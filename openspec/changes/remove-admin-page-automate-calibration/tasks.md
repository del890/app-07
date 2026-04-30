## 1. Service — Auto-calibrate on startup

- [x] 1.1 In `service/src/service/main.py` lifespan, after `ingest_from_settings(settings)`, add a guarded call to `run_calibration` via `asyncio.to_thread` (skip if `get_cached_history()` is `None`)
- [x] 1.2 Import `asyncio`, `run_calibration`, and `get_cached_history` in `main.py` where needed; add a startup log entry for calibration start/end

## 2. Service — Re-calibrate after sync

- [x] 2.1 In `service/src/service/sync/task.py`, after the hot-reload step (step 5), add step 6: call `run_calibration(get_cached_history())` when `draws_added > 0`
- [x] 2.2 Add log entries in `run_sync` for calibration start and completion (or failure) after sync

## 3. Client — Remove Admin page

- [x] 3.1 Delete `client/app/pages/admin/index.vue`
- [x] 3.2 In `client/app/layouts/default.vue`, remove the Admin nav link (`<NuxtLink to="/admin">`) and its associated `mode === 'admin'` branch from the `computed` and class bindings
