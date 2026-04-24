# service

Python 3.11+ backend for the Lotofácil prediction webapp.

- Framework: FastAPI
- Agent: Anthropic Claude (tool-use loop, never prose-derived numbers)
- Deps: `uv`
- Lint / type / test: `ruff`, `mypy --strict`, `pytest`

See [`openspec/changes/build-lotofacil-webapp/`](../openspec/changes/build-lotofacil-webapp/) for
the governing proposal, design, specs, and tasks.

## Setup

```bash
cd service
uv sync
cp ../.env.example .env        # fill in ANTHROPIC_API_KEY
```

## Run

```bash
uv run uvicorn service.main:app --reload --port 8000
```

Health: `GET /v1/health`. Readiness: `GET /v1/ready`.

## Test

```bash
uv run pytest                     # unit + integration (LLM mocked)
RUN_LIVE_LLM=1 uv run pytest -m live_llm   # live Anthropic API tests
```

## Lint & typecheck

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
```

## Layout

```
service/
├── pyproject.toml
├── src/service/
│   ├── main.py            # FastAPI app
│   ├── config.py          # pydantic-settings
│   ├── logging_config.py  # structured JSON logging
│   ├── ingestion/         # draw-data-ingestion capability
│   ├── statistics/        # statistical-analysis capability
│   ├── correlation/       # external-signal-correlation capability
│   ├── engine/            # prediction-engine (models + calibration)
│   ├── agents/            # LLM agent orchestrator
│   ├── tools/             # typed tool handlers the agent calls
│   ├── prompts/           # system prompts
│   ├── llm/               # Anthropic client factory
│   └── models/            # shared Pydantic response models
└── tests/
```

## Deployment

Single-node, reverse-proxy-friendly. Recommended stack: nginx → uvicorn.

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | **yes** | — | Anthropic API key; service refuses to start without it |
| `ENV` | no | `dev` | `dev` / `staging` / `prod` |
| `LOG_LEVEL` | no | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `DATA_JSON_PATH` | no | `../data.json` | Path to the draw dataset |
| `PREDICTIONS_RATE_LIMIT_PER_MINUTE` | no | `10` | Per-IP rate limit on `/v1/predictions/*` |
| `LLM_MONTHLY_SPEND_CAP_USD` | no | `50.0` | Advisory cap (not enforced server-side) |
| `CALIBRATION_STALE_AFTER_DAYS` | no | `14` | Days before calibration is considered stale |

`data.json` is shipped inside the Docker image (or mounted as a volume). It must
be present at startup; the service will fail fast with a clear error if it is missing.

### Docker (example)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --no-dev
COPY src/ src/
COPY ../data.json data.json
ENV DATA_JSON_PATH=/app/data.json
CMD ["uv", "run", "uvicorn", "service.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Calibration

The prediction engine must be calibrated before play-surface suggestions are available.
`GET /v1/ready` reports `calibration.ok: false` until calibration has run.

**Trigger manual recalibration (from within the service process):**
```python
from service.engine import run_calibration
from service.ingestion import get_cached_history
run_calibration(get_cached_history())
```

**Weekly cron (example):**
```cron
0 2 * * 1  curl -s -X POST http://localhost:8000/v1/admin/recalibrate
```
*(An admin endpoint for recalibration is a future task; for now, restart the service or call `run_calibration` directly.)*

Token usage since last restart is visible at `GET /v1/ready` under the `token_usage` check.

