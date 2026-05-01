## Why

The app's prediction engine derives number suggestions purely from historical draw statistics and ML models. Users often want to play based on personal qualitative experiences — dreams, vivid scenarios, nightmares — but have no way to feed that context into the system. The external-signal correlation feature is a separate research tool for time-series analysis and has no pathway to produce number suggestions; there is no overlap to reuse.

## What Changes

- Introduce a new **dream-oracle** capability: a POST endpoint that accepts a free-text scenario description, uses an LLM agent with a structured symbolic-extraction pipeline to map the narrative to a number probability bias vector, and returns 15 suggested numbers plus a per-symbol explanation.
- Define a **symbolic catalog** (color → number range, archetype → parity/sum pattern, explicit counts → direct number boosts) that makes the mapping transparent and reproducible, rather than leaving it as an opaque LLM guess.
- The LLM agent calls a new `extract_dream_signals` tool first (structured output: list of detected symbols with category and intensity), then passes the resulting bias vector to the existing `materialize_suggestion` flow so number selection reuses proven infrastructure.
- Add a new client page `/play/dream` that streams the interpretation as the agent works and presents the 15 numbers alongside the symbolic explanation.
- The feature is labelled `artifact_type: entertainment` throughout — numbers are produced from symbolic mapping, not statistical prediction.
- The external-signal correlation feature (`/research/correlations`) is **not modified**; it remains a separate research-mode statistical tool with no connection to this change.

## Capabilities

### New Capabilities
- `dream-oracle`: Accepts a natural-language scenario description; extracts structured symbolic signals via LLM; maps symbols to a bias vector over numbers 1–25 using a defined catalog; applies the existing `materialize_suggestion` pipeline; returns 15 numbers and a human-readable symbolic explanation. Labelled `artifact_type: entertainment`.

### Modified Capabilities
<!-- none -->

## Impact

- **Service**: New module `service/src/service/oracle/` (symbolic catalog, bias model, agent prompt). New tool `extract_dream_signals`. New API endpoint `POST /v1/oracle/dream`. Reuses `materialize_suggestion` from `service.tools`.
- **Client**: New page `client/app/pages/play/dream.vue`. New composable `useDreamOracle.ts`. Extends `useSsePrediction` pattern (SSE streaming). New type `DreamOracleResult` in `types/api.ts`.
- **No breaking changes** to existing endpoints or models.
- **New dependency**: None beyond what's already installed (`anthropic` SDK, `pydantic`).
