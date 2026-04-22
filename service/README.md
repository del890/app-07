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
