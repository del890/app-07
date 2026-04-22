## 1. Repo scaffolding & tooling

- [x] 1.1 Create top-level `client/` and `service/` directories (do not touch `data.json` or `openspec/`).
- [x] 1.2 Add `.gitignore` entries for `client/node_modules/`, `client/.nuxt/`, `client/.output/`, `service/.venv/`, `service/__pycache__/`, `.env`, and log/calibration artifact dirs.
- [x] 1.3 Add a top-level `README.md` pointing to `client/` and `service/` run instructions and to `openspec/` for specs.
- [x] 1.4 Add a top-level `.env.example` listing `ANTHROPIC_API_KEY` and any other required env vars; never commit real values.

## 2. Service: project bootstrap (Python, agents, LLM)

- [x] 2.1 `cd service && uv init` and create `pyproject.toml` with Python ≥ 3.11.
- [x] 2.2 Add runtime deps: `anthropic`, `fastapi`, `uvicorn`, `pydantic>=2`, `pydantic-settings`, `python-dotenv`, `numpy`, `pandas`, `scikit-learn`, `scipy`.
- [x] 2.3 Add dev deps: `ruff`, `mypy`, `pytest`, `pytest-asyncio`, `httpx` (for test client).
- [x] 2.4 Configure Ruff (lint + format), mypy strict (`disallow_untyped_defs`), and `pytest` with `tests/` discovery.
- [x] 2.5 Create src layout: `service/src/service/{__init__.py,main.py,config.py,llm/,agents/,tools/,prompts/,models/}` and `service/tests/`.
- [x] 2.6 Implement `config.py` with `pydantic-settings` loading `ANTHROPIC_API_KEY`, `ENV`, `LOG_LEVEL`, and the rate-limit / spend-cap knobs.
- [x] 2.7 Implement `llm/client.py` — Anthropic client factory with `cache_control` helpers and retry/backoff.
- [x] 2.8 Fail-fast startup: if `ANTHROPIC_API_KEY` is missing, refuse to start with a clear error (per `prediction-service-api` spec).
- [x] 2.9 Add structured JSON logging (one line per request) with request id, route, status, duration, token usage.

## 3. Capability: draw-data-ingestion

- [x] 3.1 Define `DrawRecord` Pydantic model (index, iso_date, numbers_sorted: tuple[int, ...], original_position).
- [x] 3.2 Implement `DataLoader.load(path: Path) -> DrawHistory` that reads `data.json`, validates every record (15 unique numbers in 1–25, `DD-MM-YYYY` date), converts dates to ISO-8601 once.
- [x] 3.3 Implement `DrawHistory` with chronological order, fast lookups by index, and a memoized content hash (SHA-256 of `data.json` bytes).
- [x] 3.4 Ensure ingestion is idempotent within a process (single read per lifetime).
- [x] 3.5 Implement `Provenance` model exposing count, earliest/latest ISO date, source path, content hash.
- [x] 3.6 Add ingestion to service startup; fail fast if `data.json` is missing or invalid (name the path in the error).
- [x] 3.7 Unit tests: valid load, missing file, invalid date, duplicate numbers, out-of-range number, wrong count.
- [x] 3.8 Golden test: tiny synthetic `data.json` produces expected hash + record count + first/last dates.

## 4. Capability: statistical-analysis

- [x] 4.1 Implement per-number frequency (full + rolling window N).
- [x] 4.2 Implement gap statistics: current gap, mean gap, max gap per number, plus deterministic hot/cold classification with a documented threshold.
- [x] 4.3 Implement co-occurrence counts for arities 2, 3, 4 with top-K queries (cap K and arity at sane upper bounds; memoize).
- [x] 4.4 Implement structural distributions: sum, even/odd split, per-quintile counts, min/max.
- [x] 4.5 Implement intra-draw order analysis; detect whether source data carries original order and label the result accordingly.
- [x] 4.6 Implement PI-alignment analysis with an explicit rule catalog; every result must cite the rule used.
- [x] 4.7 Attach provenance (dataset hash, window descriptor, computed_at timestamp) to every result via a shared decorator/util.
- [x] 4.8 Unit tests: hand-verified golden values for frequency, gap, one pair, one structural metric, one PI rule, on a tiny synthetic dataset.
- [x] 4.9 Property tests: frequency shares sum to 1 per window; gap mean × frequency relation holds; sorted-canonical order is stable.

## 5. Capability: external-signal-correlation

- [x] 5.1 Define `SignalSeries` Pydantic model (name, cadence, unit, source, date→value rows) with mandatory metadata validation.
- [x] 5.2 Implement file-based signal loader (CSV + JSON) under `service/signals/` with schema validation.
- [x] 5.3 Implement alignment policy (forward-fill for slower cadences, event-keyed join for calendar, configurable lag) and report it on every correlation result.
- [x] 5.4 Implement Spearman correlation + Mann–Whitney fallback for categorical metrics; return effect size + raw p-value + sample size + test used.
- [x] 5.5 Enforce minimum sample size (default 30); below it, return the result with `under_powered: true` and do not suppress.
- [x] 5.6 Implement batch correlation with Benjamini–Hochberg FDR; return both raw p-values and corrected q-values; document method in response.
- [x] 5.7 Label every result with `artifact_type: "research"` and attach the research-only disclaimer.
- [x] 5.8 Unit tests: known-correlated synthetic series returns significant, uncorrelated returns non-significant, under-powered is flagged, BH correction matches hand calc on a small batch.

## 6. Capability: prediction-engine — baseline + learned models

- [ ] 6.1 Implement frequency-recency baseline model producing a 25-length probability vector; deterministic given dataset hash.
- [ ] 6.2 Engineer features for the learned model (windowed frequencies, gaps, pair-presence flags) and persist the feature spec with a version id.
- [ ] 6.3 Train a per-number `HistGradientBoostingClassifier` (sklearn) on the oldest 80% slice; save model artifacts with a version id.
- [ ] 6.4 Ensemble baseline + learned into a single distribution; expose ensemble composition + model versions in the result.
- [ ] 6.5 Unit tests: baseline is bit-deterministic; learned model loads + predicts; ensemble sums to the expected mass (15).

## 7. Capability: prediction-engine — calibration

- [ ] 7.1 Split history: train (oldest 80%) / calibration (next 15%) / held-out eval (most recent 5%).
- [ ] 7.2 Fit isotonic regression on the calibration slice; persist the calibrator with a version id and a reliability-diagram data file.
- [ ] 7.3 Compute eval metrics on the held-out slice (Brier score, log loss, reliability curve) and persist alongside the model version.
- [ ] 7.4 Implement `CalibrationStatus` (last_calibrated_at, is_stale, reliability_curve, model_versions) queryable via a tool and via the API.
- [ ] 7.5 Gate: uncalibrated or stale engine returns research-surface predictions with `calibrated: false`, and the API refuses play-surface suggestions.
- [ ] 7.6 Tests: calibrator reduces ECE on synthetic miscalibrated inputs; stale sentinel flips after a simulated model version change.

## 8. Capability: prediction-engine — agent + tools

- [ ] 8.1 Define typed tool handlers (Pydantic-validated) for: provenance, frequency, gaps, co-occurrence, structural, PI alignment, signal correlation, next-draw distribution, suggestion materialization, scenario step advance.
- [ ] 8.2 Emit JSON-Schema tool definitions from Pydantic models; apply `cache_control` to the tool block and to the system prompt.
- [ ] 8.3 Implement the agent tool-use loop: call Claude → dispatch `tool_use` blocks → reply with `tool_result` → repeat until `end_turn`; cap tool-call count per request.
- [ ] 8.4 Enforce the invariant: every numeric value in the final output must be traceable to a tool invocation; add a post-response validator that rejects prose-derived numbers.
- [ ] 8.5 Implement scenario-path generation: each step advances via a dedicated tool that conditions on the evolving state id; path-level confidence is monotonically non-increasing with horizon.
- [ ] 8.6 Default model `claude-sonnet-4-6`; scenario generation escalates to `claude-opus-4-7`; Haiku for cheap subtasks.
- [ ] 8.7 Attach provenance on every response: dataset hash, model versions, agent prompt hash, tool trace, confidence, timestamp.
- [ ] 8.8 Serialization guard: reject responses missing `confidence` or with `confidence >= 1.0` or `confidence <= 0`.
- [ ] 8.9 Tests: replay-based unit tests for the tool loop; live integration behind `RUN_LIVE_LLM=1`; guard-rail tests verify rejection of prose-derived numbers.

## 9. Capability: prediction-service-api

- [x] 9.1 Mount all routes under `/v1/`.
- [x] 9.2 Implement `GET /v1/dataset` returning ingestion provenance.
- [x] 9.3 Implement statistical endpoints: `/v1/statistics/frequency`, `/gaps`, `/cooccurrence`, `/structural`, `/order`, `/pi-alignment`.
- [x] 9.4 Implement `POST /v1/correlations` (single) and `POST /v1/correlations/batch` (BH-corrected).
- [ ] 9.5 Implement `POST /v1/predictions/next-draw` and `POST /v1/predictions/scenario-path`, each supporting JSON and SSE via `Accept`.
- [ ] 9.6 Implement SSE streaming of agent events (tool start, tool result, final) via FastAPI `StreamingResponse`.
- [x] 9.7 Implement `GET /v1/health` (liveness) and `GET /v1/ready` (readiness: ingestion done + calibration fresh; 503 otherwise with a body describing the missing precondition).
- [x] 9.8 Implement the canonical error envelope `{ "error": { "code", "message", "details" } }` and map status codes (400/404/409/429/5xx).
- [ ] 9.9 Implement per-client rate limit on `/v1/predictions/*` with `Retry-After`.
- [x] 9.10 Wire structured request logging (request id, route, status, duration, dataset hash, model versions, tool-call count, token usage).
- [x] 9.11 Ensure `ANTHROPIC_API_KEY` never appears in responses, logs, or stack traces; add a test that asserts this.
- [x] 9.12 Integration tests via FastAPI `TestClient`: each route returns the expected shape, error envelope, and headers.

## 10. Client: project bootstrap (Nuxt + TypeScript)

- [ ] 10.1 `cd client && npx nuxi@latest init .` (Nuxt 3+).
- [ ] 10.2 Enable TypeScript strict + typeCheck in `nuxt.config.ts`; extend `./.nuxt/tsconfig.json` in `tsconfig.json`.
- [ ] 10.3 Set `ssr: false` for v1 (SPA mode).
- [ ] 10.4 Install and configure Tailwind CSS (per design decision); no mixing with scoped CSS for primary styling.
- [ ] 10.5 Install Chart.js + `vue-chartjs` (per design decision).
- [ ] 10.6 Add eslint + prettier with project presets; enforce no `.js` source files (lint rule).
- [ ] 10.7 Configure `runtimeConfig.public.apiBase` to point at the service; expose as `useRuntimeConfig()` in composables.
- [ ] 10.8 Add base `layouts/default.vue` with a persistent mode indicator (research vs play) and the research/entertainment disclaimer.

## 11. Client: shared data layer

- [ ] 11.1 Create typed API client under `client/app/composables/useApi.ts` wrapping `useFetch` with error-envelope handling.
- [ ] 11.2 Define shared types for all API responses under `client/app/types/api.ts` (keep in sync with service Pydantic models).
- [ ] 11.3 Implement `useDatasetProvenance()` composable (cached globally).
- [ ] 11.4 Implement `useSsePrediction()` composable wrapping `EventSource` for streaming prediction endpoints with automatic fallback to JSON on connection failure.
- [ ] 11.5 Implement `<ConfidenceBadge>` component that renders a 0–1 score prominently and refuses to render if confidence is missing or ≥ 1.0.

## 12. Client: research mode

- [ ] 12.1 Route `/research` with an index grid linking to each view.
- [ ] 12.2 Frequency view: per-number bar chart, window selector (full / rolling N), dataset hash + window displayed.
- [ ] 12.3 Gap / hot-cold view: table + chart, threshold documented in-UI.
- [ ] 12.4 Co-occurrence explorer: arity selector (2/3/4), top-K table, click-through to highlight draws containing the combination.
- [ ] 12.5 Structural distributions view: histograms for sum, even/odd, quintiles, min/max.
- [ ] 12.6 Order-analysis view; clearly label whether order is original-drawn or sorted-canonical.
- [ ] 12.7 PI-alignment view: choose rule, choose target (single draw or window), render score + explanation.
- [ ] 12.8 External-signal correlation explorer: pick signal + draw metric + lag; single and batch modes; hide numeric effect when significance is unavailable.
- [ ] 12.9 All research views display `artifact_type: "research"` disclaimer for correlation outputs.

## 13. Client: play mode

- [ ] 13.1 Route `/play` with a primary CTA for "Suggest next draw".
- [ ] 13.2 On request, call `POST /v1/predictions/next-draw` with SSE; render tool calls as they stream in.
- [ ] 13.3 Render the 15-number suggestion alongside a `<ConfidenceBadge>` and human-readable explanation.
- [ ] 13.4 Scenario-path view: select horizon H, render each predicted draw and the monotonically non-increasing path confidence.
- [ ] 13.5 If the API reports `calibrated: false` or returns a stale-calibration error, do NOT render a suggestion; show an explanatory banner and a link to research mode.
- [ ] 13.6 Persistent "research/entertainment only" copy; ban words "guaranteed", "winning", "sure" via a simple copy-lint script run in CI.

## 14. Client: cross-cutting

- [ ] 14.1 Responsive layout verified at 360px, 768px, 1280px.
- [ ] 14.2 WCAG 2.1 AA: color contrast, keyboard navigation, focus states on all interactive controls.
- [ ] 14.3 Vitest unit tests for composables (`useApi`, `useSsePrediction`) and `<ConfidenceBadge>`.
- [ ] 14.4 Playwright end-to-end: research-mode frequency view loads; play-mode calibrated prediction renders; play-mode refuses when uncalibrated.

## 15. Observability, ops & docs

- [ ] 15.1 Service: emit the structured request log fields described in §9.10; add a log-redaction test that asserts no secrets leak.
- [ ] 15.2 Service: expose token-usage counters and last-calibration timestamp via `/v1/ready`.
- [ ] 15.3 Define a weekly calibration cron + on-start calibration check; document how to trigger a manual recalibration.
- [ ] 15.4 Document deployment shape (single-node, reverse proxy, env vars, data.json shipped with image) in `service/README.md` and `client/README.md`.
- [ ] 15.5 Document the agent tool contract + invariants ("no prose-derived numbers") in `service/docs/agent.md`.
- [ ] 15.6 Confirm the project's `client-stack` and `service-stack` skills are still accurate; update them if decisions drifted during implementation.

## 16. Acceptance checks against the specs

- [ ] 16.1 Walk every requirement in `specs/draw-data-ingestion/spec.md` and tick off its covering test/route.
- [ ] 16.2 Walk every requirement in `specs/statistical-analysis/spec.md` and tick off its covering test/route.
- [ ] 16.3 Walk every requirement in `specs/external-signal-correlation/spec.md` and tick off its covering test/route.
- [ ] 16.4 Walk every requirement in `specs/prediction-engine/spec.md` and tick off its covering test/route.
- [ ] 16.5 Walk every requirement in `specs/prediction-service-api/spec.md` and tick off its covering test/route.
- [ ] 16.6 Walk every requirement in `specs/research-webapp/spec.md` and tick off its covering test/view.
- [ ] 16.7 Run `openspec validate --change build-lotofacil-webapp` and resolve any findings before calling the change done.
