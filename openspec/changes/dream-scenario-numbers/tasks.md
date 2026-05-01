## 1. Service: Symbolic Catalog

- [x] 1.1 Create `service/src/service/oracle/` package with `__init__.py`.
- [x] 1.2 Define `BiasRule` Pydantic model (`numbers: list[int]`, `multiplier: float`, `rationale: str`) in `service/src/service/oracle/catalog.py`.
- [x] 1.3 Implement the v1 symbolic catalog dict mapping `(category, label) → BiasRule` covering: `element` (water, fire, earth, air, void), `color` (red, orange, yellow, green, blue), `emotion` (joy, fear, calm, rage), `archetype` (falling, flying, chasing, hiding), and `count` (integers 1–25).
- [x] 1.4 Export `CATALOG_VERSION = "1.0"` constant from `catalog.py`.
- [x] 1.5 Write unit tests in `service/tests/test_oracle_catalog.py` covering: known (category, label) pairs return correct number sets; unknown pair returns `None`; `CATALOG_VERSION` is a non-empty string.

## 2. Service: Bias Vector Builder

- [x] 2.1 Implement `build_bias_vector(symbols: list[ExtractedSymbol], *, max_symbols: int = 8) → list[float]` in `service/src/service/oracle/bias.py`. Input: list of `ExtractedSymbol(category, label, intensity)`; output: 25-length vector summing to 15.0.
- [x] 2.2 Implement top-8-by-intensity truncation logic inside `build_bias_vector`.
- [x] 2.3 Implement normalization so the vector sums to exactly 15.0 before return.
- [x] 2.4 Handle unknown `(category, label)` pairs gracefully (skip and log a warning).
- [x] 2.5 Write unit tests in `service/tests/test_oracle_bias.py` covering: vector length is always 25; vector sum is always 15.0; top-8 truncation; unknown symbol is skipped.

## 3. Service: extract_dream_signals Tool

- [x] 3.1 Define `ExtractedSymbol` Pydantic model (`category: str`, `label: str`, `intensity: float` in [0,1]) in `service/src/service/oracle/models.py`.
- [x] 3.2 Define `DreamOracleResult` Pydantic model (`numbers: list[int]`, `explanation: str`, `symbols: list[ExtractedSymbol]`, `catalog_version: str`, `artifact_type: Literal["entertainment"]`, `disclaimer: str`) in `service/src/service/oracle/models.py`.
- [x] 3.3 Implement the `extract_dream_signals` tool handler in `service/src/service/oracle/tools.py`: accepts `{ "description": str }`, returns `{ "symbols": [...] }` in the tool-dispatch pattern.
- [x] 3.4 Register `extract_dream_signals` in the oracle agent's tool definitions (separate from the prediction engine's tool definitions).

## 4. Service: Oracle Agent

- [x] 4.1 Write the oracle system prompt in `service/src/service/oracle/prompt.py` that (a) forbids emitting numbers without calling `extract_dream_signals` first, (b) instructs the agent to call `materialize_suggestion` after building the bias vector, (c) requires the final answer as JSON matching `DreamOracleResult`.
- [x] 4.2 Implement `interpret_dream(description: str, *, model: str = DEFAULT_MODEL, streaming: bool = False) → dict | Iterator[dict]` in `service/src/service/oracle/agent.py` using the Anthropic SDK tool-use loop pattern from `service/src/service/agents/__init__.py`.
- [x] 4.3 Implement the agent validator that checks the tool trace contains `extract_dream_signals` before `materialize_suggestion`; raise an internal error if the order is violated.
- [x] 4.4 Reuse `materialize_suggestion` from `service.tools` — pass the bias vector as a distribution (wrapped as a `NextDrawDistribution`-compatible object with `distribution_id`).
- [x] 4.5 Ensure the raw `description` string is never written to any log file or persistent store.
- [x] 4.6 Write unit tests in `service/tests/test_oracle_agent.py` covering: valid description returns 15 numbers; tool trace order is validated; `artifact_type` is `"entertainment"` on every result.

## 5. Service: API Endpoint

- [x] 5.1 Define `DreamRequest` Pydantic model (`description: str = Field(min_length=1, max_length=2000)`) in `service/src/service/api/oracle.py`.
- [x] 5.2 Implement `POST /v1/oracle/dream` endpoint supporting both `application/json` and `text/event-stream` responses, following the same SSE pattern as `service/src/service/api/predictions.py`.
- [x] 5.3 Register the oracle router under the `/v1` prefix in the main FastAPI app.
- [ ] 5.4 Write integration tests in `service/tests/test_api.py` (or a new `test_oracle_api.py`) covering: valid description returns 200 with 15 numbers; empty description returns 422; description over 2000 chars returns 422; `artifact_type` is `"entertainment"`.

## 6. Client: Types and Composable

- [x] 6.1 Add `DreamOracleResult` interface to `client/app/types/api.ts` matching the service model (`numbers`, `explanation`, `symbols`, `catalog_version`, `artifact_type: 'entertainment'`, `disclaimer`).
- [x] 6.2 Create composable `client/app/composables/useDreamOracle.ts` that wraps the SSE streaming pattern from `useSsePrediction` for `POST /v1/oracle/dream`.

## 7. Client: Dream Oracle Page

- [x] 7.1 Create `client/app/pages/play/dream.vue` with a textarea for the scenario description, a submit button, and the entertainment disclaimer always visible.
- [x] 7.2 Stream agent tool events using `useDreamOracle` and render them as they arrive (reuse `ToolProgressTimeline` component if applicable).
- [x] 7.3 On completion, render the 15 suggested numbers in the same visual style as `next-draw.vue`.
- [x] 7.4 Render the `symbols` list with each symbol's category, label, intensity, and the rationale from the catalog below the numbers.
- [x] 7.5 Add a link to `/play/dream` from the play index page (`client/app/pages/play/index.vue`) with a brief description.
- [x] 7.6 Ensure no banned words ("garantido", "garantida", "certeza", "winning", "guaranteed", "sure") appear in the page copy; add the page to the copy-lint script (`client/scripts/copy-lint.js`).
