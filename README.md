# Lotofácil Prediction Webapp

A research + prediction webapp over a 22-year historical Lotofácil dataset (3,656 draws).
Two services joined by an HTTP API:

- [`service/`](service/) — Python 3.11+, FastAPI, agent-first (Anthropic Claude) backend that owns data ingestion, statistical analysis, external-signal correlation, and the prediction engine.
- [`client/`](client/) — Nuxt 3 + TypeScript (strict) research/play UI.

The dataset lives in [`data.json`](data.json) at the repo root and is treated as immutable input.
All design, specs, and tasks are tracked in [`openspec/`](openspec/) — see the active change
[`openspec/changes/build-lotofacil-webapp/`](openspec/changes/build-lotofacil-webapp/).

## Prerequisites

- Python ≥ 3.11 (install via `uv python install 3.11` if needed)
- [`uv`](https://docs.astral.sh/uv/) for Python dependency management
- Node ≥ 20 (Node 22+ recommended) with `npm` / `npx`
- An `ANTHROPIC_API_KEY` (required at runtime; see `.env.example`)

## Running the service

```bash
cd service
uv sync
cp ../.env.example .env        # fill in ANTHROPIC_API_KEY
uv run uvicorn service.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/v1/health`.

## Running the client

```bash
cd client
npm install
npm run dev
```

## Running tests

```bash
# service
cd service && uv run pytest

# client
cd client && npm run test
```

## Project conventions

- Client stack is enforced by the [`client-stack`](.claude/skills/client-stack/SKILL.md) skill:
  Nuxt 3 + TypeScript strict, no plain JS sources.
- Service stack is enforced by the [`service-stack`](.claude/skills/service-stack/SKILL.md) skill:
  Python 3.11+, agent-first, LLM-powered (Anthropic Claude).
- All new work goes through [OpenSpec](openspec/) — propose a change, generate specs & tasks,
  then `/opsx:apply` to implement.

## Non-goals

Lotofácil only (no generalization). No user accounts, no real-money integration, no betting
automation. Predictions are research/entertainment artifacts — the system must never claim
certainty. See [`design.md`](openspec/changes/build-lotofacil-webapp/design.md).
