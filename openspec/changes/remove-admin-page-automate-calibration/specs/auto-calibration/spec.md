## ADDED Requirements

### Requirement: Service auto-calibrates on startup
The service SHALL run the calibration pipeline automatically during startup, immediately after dataset ingestion completes, if the engine is stale (never calibrated or calibration is older than the staleness threshold).

#### Scenario: First startup with no prior calibration
- **WHEN** the service starts for the first time and `data.json` is loaded
- **THEN** calibration runs automatically before the service accepts requests
- **THEN** `GET /v1/ready` returns HTTP 200 with `calibration.ok = true`

#### Scenario: Restart with fresh calibration
- **WHEN** the service restarts and the existing calibration artifact is still fresh
- **THEN** calibration is skipped (no unnecessary recompute)
- **THEN** `GET /v1/ready` still returns HTTP 200

#### Scenario: Ingestion fails on startup
- **WHEN** `data.json` is missing or unreadable
- **THEN** calibration SHALL be skipped
- **THEN** the service starts but `GET /v1/ready` returns a non-OK status reflecting the ingestion failure

### Requirement: Service re-calibrates after successful dataset sync
The service SHALL automatically run calibration after each dataset sync that adds at least one new draw.

#### Scenario: Sync adds new draws
- **WHEN** the periodic sync job completes successfully and adds ≥ 1 new draws
- **THEN** calibration runs automatically after the in-memory dataset is reloaded
- **THEN** the updated calibration is reflected in subsequent `GET /v1/ready` responses

#### Scenario: Sync is a no-op
- **WHEN** the sync job runs but no new draws are available
- **THEN** calibration SHALL NOT be triggered (no unnecessary work)

### Requirement: Admin page is removed
The client application SHALL NOT expose a `/admin` route or any UI for manually triggering calibration.

#### Scenario: Navigation has no Admin link
- **WHEN** the application loads
- **THEN** the navigation bar SHALL NOT contain an "Admin" or "Configuração" link

#### Scenario: Direct navigation to /admin
- **WHEN** a user navigates directly to `/admin`
- **THEN** Nuxt's default 404 page SHALL be shown (no admin UI is rendered)
