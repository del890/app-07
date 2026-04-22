## Why

The project owns a 22-year historical dataset of Lotofácil draws (3,656 entries in `data.json`) but has no system for analyzing it, researching patterns against external world signals, or generating confidence-scored predictions. Today the data just sits there — we cannot answer research questions (do draws align with PI digits? do they correlate with market/earth/event signals? what is the order structure?) nor can we produce actionable, honest number suggestions for play. This change bootstraps the full stack — ingestion, analysis, prediction engine, service API, and research webapp — so the dataset becomes a living research and prediction tool rather than a static file.

## What Changes

- Introduce a canonical **draw-data ingestion** pipeline that loads `data.json`, validates schema (3,656 draws, DD-MM-YYYY, 15 numbers per draw from 1–25), and exposes a normalized in-memory / cached representation to downstream capabilities.
- Build a **statistical analysis** capability covering frequency, gap, hot/cold, pair/triplet/quadruplet co-occurrence, order analysis within a draw, parity/sum/range distributions, and alignment checks against external constants (PI digits, etc.).
- Build an **external-signal correlation** capability that ingests world-event / market / earth-position / calendar signals and measures correlation against draw patterns, with explicit statistical significance checks (no false positives masquerading as signal).
- Build a **prediction engine** that combines statistical and ML models (baseline Markov + frequency, plus learned models) with an agent-driven meta-layer that produces next-draw probability distributions, multi-draw **self-consistent scenario paths**, and a calibrated **confidence score** on every output.
- Expose a **prediction service API** (Python, agent-based per the service stack) so the client and future consumers can request analyses, predictions, and scenarios over HTTP.
- Build a **research webapp** (Nuxt + TypeScript per the client stack) with two modes: a research surface for rigorous pattern exploration and a play surface for actionable number suggestions. All predictions shown in the UI must display their confidence score — no false certainty.

No breaking changes: greenfield build.

## Capabilities

### New Capabilities

- `draw-data-ingestion`: Load, validate, and normalize the Lotofácil historical dataset from `data.json` and expose it as the single source of truth for all downstream analysis.
- `statistical-analysis`: Run deterministic statistical and pattern-research analyses over the draw history (frequency, gaps, co-occurrence, order, PI alignment, sum/parity/range distributions).
- `external-signal-correlation`: Ingest external world signals (events, markets, earth position, calendars) and measure their correlation with draw patterns with explicit significance testing.
- `prediction-engine`: Produce next-draw probability distributions and multi-draw self-consistent scenario paths, combining statistical baselines, ML models, and an LLM-agent meta-layer, each output tagged with a calibrated confidence score.
- `prediction-service-api`: HTTP API (Python, agent-backed) that exposes ingestion, analysis, correlation, and prediction capabilities to clients.
- `research-webapp`: Nuxt + TypeScript web UI providing a research mode (pattern exploration, visualizations) and a play mode (actionable number suggestions), always surfacing confidence scores.

### Modified Capabilities

None — this is the initial build and there are no existing capability specs to modify.

## Impact

- **Code**: Creates two new top-level trees in the repo — `client/` (Nuxt + TypeScript) and `service/` (Python, agent-based). No existing code is affected.
- **Data**: Reads `data.json` (read-only primary source). Introduces a cached / normalized derivative dataset used by the analysis and prediction capabilities.
- **APIs**: Introduces a new HTTP surface exposed by the service (`prediction-service-api`). The client consumes it; no external consumers yet.
- **Dependencies**:
  - Client: Nuxt 3+, TypeScript (strict), a charting library for research visualizations (to be decided in design.md), one styling approach (Tailwind/UnoCSS/SFC — decided in design).
  - Service: Python 3.11+, Anthropic SDK (Claude), FastAPI + Uvicorn, Pydantic v2, NumPy/Pandas for statistics, scikit-learn (and possibly a lightweight gradient-boosted or sequence model) for ML, `uv` for dependency management, Ruff + mypy + pytest.
- **Systems / Operational**: Requires an `ANTHROPIC_API_KEY` secret for the service. No other external services are required for the initial build; external-signal sources will be stubbed / file-based until a live ingestion path is justified.
- **Non-goals (explicit)**: No user accounts, no betting automation, no real-money integration, no multi-lottery generalization. Predictions are research/entertainment artifacts — the system must never claim certainty.
