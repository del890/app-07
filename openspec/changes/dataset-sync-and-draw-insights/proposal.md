## Why

The Lotofácil dataset is static — it lives in `data.json` and is never automatically refreshed, so the service operates on stale data as soon as new draws are conducted. Additionally, the play mode offers no way for users to enter draws they already hold and immediately see personalized statistical context (how frequently their numbers have appeared, whether the combination is already in the dataset, co-occurrence strength, etc.). These two gaps together prevent the service from being useful to an active lottery player.

## What Changes

- Introduce an **automatic dataset sync** capability that fetches the latest Lotofácil draws from a public internet source on a configurable schedule, merges them into the dataset, and persists the updated `data.json` without manual intervention.
- Extend the **draw-data-ingestion** capability so it can reload the dataset after an external sync without restarting the service process; downstream consumers must see fresh data on the next request.
- Add a **user-draw lookup** capability (client-side play section) where users can enter a set of 15 numbers, receive a statistical profile of that number set derived from the full history, and be informed if the exact draw already exists in the dataset.

## Capabilities

### New Capabilities

- `dataset-auto-sync`: Periodically fetch the latest Lotofácil results from an authoritative public internet source, validate and merge new draws into `data.json`, and trigger an in-process dataset reload so the service is always current without restarts.
- `user-draw-insights`: Client-side page (under `/play`) where the user manually enters 15 numbers, then receives: frequency stats for each chosen number, pairwise co-occurrence stats for the chosen combination, sum/parity/range distribution context, and a flag if this exact draw already exists in the historical dataset.

### Modified Capabilities

- `draw-data-ingestion`: The ingestion layer must support hot-reload — re-reading `data.json` from disk and refreshing the in-memory `DrawHistory` after a sync event, without requiring a full process restart.

## Impact

- **Service**: New background task / scheduler (e.g., APScheduler or a lightweight asyncio loop) that calls an external Lotofácil results API or scrapes the official source. The `DrawHistory` singleton must expose a `reload()` method; the existing API endpoints remain unchanged.
- **Client**: New `/play/my-draw` page with a 25-number grid selector (exactly 15 must be chosen, mirroring the game rules), a submit action that calls existing statistics API endpoints with the user's selection, and a result panel showing frequency/co-occurrence/structural stats plus a dataset-match banner if applicable.
- **Data**: `data.json` transitions from a static file to a writable, auto-updated file. A backup or diff log strategy should be considered.
- **APIs**: No new API endpoints required for user-draw-insights (reusing existing statistics endpoints). The dataset-auto-sync may expose a `POST /admin/sync` endpoint for manual triggers and a `GET /admin/sync/status` for reporting.
- **Dependencies**: Service may add `httpx` (already a likely transitive dep) and `apscheduler` or equivalent. Client adds no new libraries — uses existing composables.
- **External**: Depends on the availability of a public Lotofácil results endpoint (e.g., the official Caixa Econômica Federal API or a reliable community mirror). Fallback behavior must be defined for when the external source is unreachable.
