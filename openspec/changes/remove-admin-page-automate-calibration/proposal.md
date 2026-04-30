## Why

The Admin page exists solely to let a developer manually trigger calibration before the Play mode works. This is an unnecessary operational step that adds friction and is easy to forget — the service already has all the information it needs to calibrate itself on startup.

## What Changes

- **Automate calibration on service startup**: after ingestion completes, automatically run calibration if the engine is stale (never run or older than 14 days).
- **Schedule periodic re-calibration**: after each successful dataset sync, trigger a calibration run so the engine stays fresh automatically.
- **Remove the Admin page** (`client/app/pages/admin/index.vue` and the `/admin` route from the nav): it no longer serves a purpose once calibration is automated.
- Remove the "Atualizar" readiness panel (the `/v1/ready` diagnostic was only useful alongside the manual calibration button).
- The `POST /v1/calibrate` and `GET /v1/calibrate/status` endpoints are **kept** — they remain useful for debugging and CI health checks; only the UI is removed.

## Capabilities

### New Capabilities

- `auto-calibration`: Service self-calibrates on startup and after each sync; no human action required to make Play mode available.

### Modified Capabilities

<!-- No existing spec-level requirements change; the Play surface already declares it needs calibration — it just won't be blocked by a missing manual step. -->

## Impact

- **Service** (`service/src/service/main.py`, `service/src/service/sync/task.py`): startup lifespan gains a calibration step; sync task triggers re-calibration on success.
- **Client** (`client/app/pages/admin/`, `client/app/layouts/default.vue`): Admin page deleted; nav link removed.
- No external API changes; no new dependencies.
