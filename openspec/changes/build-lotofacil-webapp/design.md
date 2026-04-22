## Context

We are building a Lotofácil research-and-prediction webapp on top of a 22-year historical dataset (3,656 draws, `data.json`). The proposal defined six capabilities: `draw-data-ingestion`, `statistical-analysis`, `external-signal-correlation`, `prediction-engine`, `prediction-service-api`, and `research-webapp`. The requirements emphasize two things: (1) rigorous research outputs with explicit significance — no false positives — and (2) honest predictions that always carry a calibrated confidence score.

The project already has two skills that fix the stack:

- **`client-stack`** — client is **Nuxt 3+ + TypeScript (strict)**. No other frameworks, no `.js` sources.
- **`service-stack`** — service is **Python 3.11+, agent-first, LLM-powered (Anthropic Claude)**, with FastAPI + Pydantic v2 + `uv`.

This is a greenfield build — no existing code, no existing API consumers, no migration. The constraints worth naming upfront: the dataset is small (3,656 rows × 15 numbers), so model training is fast and cheap; the real risks are *statistical* (p-hacking, under-powered correlations, over-confident predictions) and *product* (framing predictions as guarantees).

## Goals / Non-Goals

**Goals:**

- Two cleanly separated services — a **Python `service/`** (agent + LLM + analysis) and a **Nuxt `client/`** (research + play UI) — joined by a versioned HTTP API.
- Single source of truth for draw history: one ingestion layer, one content-hash, propagated into every downstream result.
- Agent-first prediction engine where the LLM orchestrates deterministic tools rather than generating numbers in prose.
- Honest statistics: multiple-comparisons correction, explicit significance on every correlation, calibrated confidence on every prediction.
- Reproducibility: every numeric output can be traced back via `(dataset_hash, model_versions, agent_prompt_hash, tool_trace)`.
- A UI that makes confidence as visible as the numbers, and that refuses to show uncalibrated predictions in play mode.

**Non-Goals:**

- No user accounts, auth, persistence of per-user state, or multi-tenant concerns.
- No real-money integration, betting automation, or affiliate plumbing.
- No multi-lottery generalization — Lotofácil only. Abstracting for future lotteries is out of scope.
- No live market/astronomy data feeds in v1 — external signals are ingested from CSV/JSON files.
- No mobile-native app — responsive web only.
- No horizontal scaling / multi-node deployment concerns — v1 targets a single-node deployment.

## Decisions

### 1. Repo layout: two top-level trees, no monorepo tooling

```
/
├── data.json                        # immutable source
├── openspec/                        # already present
├── client/                          # Nuxt 3 + TS (per client-stack skill)
└── service/                         # Python + agents (per service-stack skill)
```

**Why**: A monorepo manager (Nx, Turborepo, pnpm workspaces) buys nothing at this scale and adds onboarding cost. Two trees with independent toolchains (`uv` on the Python side, `npm` on the Nuxt side) is simpler and still lets each side evolve independently. **Alternative rejected**: pnpm workspaces — overhead is not justified by any cross-package code sharing; there is none planned.

### 2. Client framework: Nuxt 3 (SSR-capable), but initially SPA mode

**Why**: Enforced by the `client-stack` skill. Within Nuxt we start in SPA mode (`ssr: false`) because the app is a logged-out, read-only research tool with no SEO requirement and the prediction endpoints are LLM-backed (slow, streaming). SSR on a streaming LLM endpoint is net negative. We keep SSR available for later marketing surfaces. **Alternative rejected**: Plain Vite + Vue — loses Nuxt's routing, data-fetching, and Nitro conventions that we want from day one.

### 3. Service framework: FastAPI + Nitro-free Python, `uv` for deps

**Why**: Enforced by the `service-stack` skill. FastAPI is the obvious choice for typed JSON APIs in modern Python and pairs cleanly with Pydantic v2 models. `uv` is significantly faster than `pip`/`poetry` and has become the de facto modern tool. **Alternative rejected**: Flask (weaker typing story), Django (wrong shape — we have no ORM/CRUD needs).

### 4. Agent design: explicit tool-use loop, no prose-derived numbers

The prediction agent is a tool-use loop around Claude. Tools are typed Python handlers exposed as JSON Schema via Pydantic. The agent never emits numeric predictions inline — it calls tools that do so, then composes and explains. This is a *hard rule* (see `prediction-engine` spec: "Agent uses tools, not prose, to compute numbers").

Tool surface (first cut):

- `get_dataset_provenance()`
- `get_frequency(window: int | "full")`
- `get_gap_statistics()`
- `get_cooccurrence(arity: 2|3|4, top_k: int)`
- `get_structural_distributions()`
- `get_pi_alignment(target: draw_index | window)`
- `get_signal_correlation(signal: str, metric: str, lag: int)`
- `get_next_draw_distribution(ensemble: str)`  → calls baseline + learned model
- `materialize_suggestion(distribution_id: str, k: int)`
- `advance_scenario_step(state_id: str)`

**Why tools, not a planner prompt**: makes the math auditable. Every number in the output maps to a tool invocation with typed inputs and deterministic outputs.

### 5. Model strategy: dual models + Claude as meta-layer

- **Baseline (deterministic)**: frequency + recency weighted prior over the 25 numbers. Fast, reproducible, great sanity check.
- **Learned model**: start with a gradient-boosted classifier per number (scikit-learn's `HistGradientBoostingClassifier`) using windowed features (recent frequencies, gaps, pair flags). Rationale: small dataset (~3.6k rows) makes any deep sequence model over-parameterized; GBM gives strong performance and cheap retraining.
- **Meta-layer**: Claude orchestrates — picks ensemble weights, applies signal-correlation adjustments (only when significant), and narrates the explanation. Claude's numeric output is always the result of a tool, never raw sampling.

Default model: `claude-sonnet-4-6` (per project guidance). Escalate to `claude-opus-4-7` for scenario-path generation where reasoning depth matters more than latency. **Alternative rejected**: LSTM / transformer on draw sequences — dataset is too small; the cost/benefit is bad.

### 6. Confidence calibration: isotonic regression on a held-out tail

Split the history into train (oldest 80%), calibration (next 15%), and held-out eval (most recent 5%). Fit the learned model on train. Use isotonic regression on the calibration slice to map raw model scores to calibrated probabilities. Recompute calibration whenever models or features change, and **refuse to serve play-surface predictions** when calibration is stale (>14 days old or a model has changed since).

**Why isotonic, not Platt**: we do not assume a sigmoid shape, and the dataset is large enough to support nonparametric calibration. **Alternative rejected**: skip calibration and emit raw model probabilities — directly violates the "no false certainty" requirement.

### 7. External signals: file-backed first, live later

v1 accepts signals as CSV/JSON files under `service/signals/`. A signal registry validates metadata (name, cadence, unit, source) and exposes an aligned view against the draw timeline. Live adapters (markets, ephemeris) are deferred until a specific signal proves its worth on file-based history. **Why**: avoids building infrastructure for signals that never move the needle. Research-first, infra-second.

Correlation tests default to Spearman (rank-based, robust to the non-normal distributions we expect) with a minimum sample size of 30 aligned pairs before a result is returned as significant. Multi-comparison correction uses Benjamini–Hochberg (FDR) when a caller runs a batch.

### 8. Streaming transport: SSE, not WebSockets

Predictions stream via Server-Sent Events. FastAPI's `StreamingResponse` forwards the Anthropic SDK's streaming events (one SSE event per upstream event), plus synthetic events for tool start / tool result. **Why SSE**: one-way server→client, HTTP-native, proxy-friendly, trivial on the Nuxt side via `EventSource`. **Alternative rejected**: WebSockets — bidirectional plumbing we do not need.

### 9. Prompt caching and cost control

Apply `cache_control` to the system prompt and the tool schema block on every Claude call, per the `claude-api` skill. Tool outputs that are large (full draw history) are summarized before inclusion — the agent requests slices, not the raw 3,656-row dump. Budget: a per-client rate limit on `/predictions/*` (default 10 req/min) and a global monthly spend cap surfaced in `/ready`.

### 10. Error envelope + versioning + observability

- All API paths under `/v1/`.
- Single error envelope: `{ "error": { "code", "message", "details" } }`.
- Structured logs (JSON, one line per request) with request id, route, status, duration, dataset hash, model versions, tool-call count, and token usage.
- `/health` (liveness) and `/ready` (readiness — 503 until ingestion and calibration are ready).

### 11. Testing: pytest + Vitest, live LLM behind a flag

- Service: `pytest` under `service/tests/`. Mock the Anthropic client in unit tests (fixture that replays recorded events). A small set of live integration tests runs behind `RUN_LIVE_LLM=1` and is excluded from CI by default.
- Statistical correctness is tested against hand-verified golden values on a tiny synthetic dataset, not just "does it run."
- Client: Vitest for composables and logic; Playwright for two critical flows — research-mode frequency view, play-mode calibrated prediction.

## Risks / Trade-offs

- **[Risk] Spurious correlations across many signals × many metrics** → Mitigation: required Benjamini–Hochberg FDR in batch mode, per-result p-value *and* q-value, `under_powered: true` flag below min sample size, and a product-level ban on correlation results appearing in play mode. The `external-signal-correlation` spec's "research artifact" label is load-bearing.
- **[Risk] Users reading predictions as guarantees** → Mitigation: confidence is a first-class UI element, persistent disclaimers, no "guaranteed"/"winning" copy, uncalibrated engine is *refused* in play mode (not softly warned).
- **[Risk] LLM prose silently producing numbers** → Mitigation: tool-use-only contract, every response carries the tool trace, serialization validation rejects predictions without provenance or confidence.
- **[Risk] Model calibration drift as new draws arrive** → Mitigation: stale-calibration sentinel in `/ready`; scheduled recalibration job (cron or on-startup check) that refuses play-surface traffic until complete.
- **[Risk] Overfitting on 3,656 rows** → Mitigation: deliberately simple GBM with regularization, held-out tail never touched during training or calibration, publish eval metrics alongside the model version.
- **[Risk] Cost spike from long agent loops** → Mitigation: prompt caching enforced, per-client rate limit, monthly spend cap in `/ready`, bound on tool-call count per request.
- **[Trade-off] Two top-level trees (no monorepo manager)** → Slightly more duplication for env config and CI wiring, but zero onboarding overhead and no tool lock-in. Worth it at this size.
- **[Trade-off] SSE instead of WebSockets** → No bidirectional control channel. Acceptable; we have no server→client *and* client→server streaming need.
- **[Trade-off] SPA-first Nuxt (`ssr: false`)** → Worse SEO, slower first paint on marketing routes. Acceptable; there is no marketing surface in v1 and SSR over LLM endpoints is counterproductive.
- **[Trade-off] File-backed signals in v1** → Limits how fresh signals can be, but avoids building integrations we might throw away.

## Migration Plan

Greenfield build — no migration of existing users, data, or APIs.

Deployment shape for v1:

1. Single-node deployment: Nuxt static build served by a CDN or Nitro preset; Python service behind a reverse proxy.
2. `ANTHROPIC_API_KEY` provisioned via environment.
3. `data.json` shipped with the service image (it is versioned in-repo; no external fetch).
4. Rollback: revert to the previous service image; the client is a static bundle, previous versions can be re-published trivially.

No phased rollout is needed; no live traffic exists.

## Open Questions

- **Signal sources for v1 bootstrap**: which specific CSV signals do we want to seed with (e.g., IBOVESPA close, USD/BRL, moon phase, Brazilian holiday calendar)? Owner: product/user. We can ship the loader without seed data, but without seeds the correlation UI has nothing to demonstrate.
- **Charting library**: the proposal deferred this. Leading options are Chart.js (lightweight, easy), ECharts (powerful, heavier), or Observable Plot (great defaults, newer). Recommend: Chart.js for v1; revisit if the research mode needs richer visuals.
- **Styling approach**: Tailwind vs UnoCSS vs scoped SFC. Recommend: Tailwind for velocity and ecosystem. Decision should be made before scaffolding the client.
- **Ensemble weights**: fixed vs agent-picked? Simpler to start with fixed (e.g., 0.4 baseline / 0.6 learned) and let the agent adjust only via the signal-correlation adjustment channel. Revisit once we have eval metrics.
- **Calibration cadence**: on every service start vs on a cron? Recommend: on start + weekly cron; check staleness timestamp at `/ready`.
- **Retention of tool traces**: how long do we keep per-request tool traces for debugging? Recommend: 7 days, in-process only (no external log store in v1).
