# Agent Tool Contract

This document describes the invariants and contract for the LLM prediction agent
defined in `service/src/service/agents/__init__.py`.

## Overview

The agent is a tool-use loop over the Anthropic API. It:
1. Receives a system prompt describing the task and required output schema.
2. Calls Claude (`claude-sonnet-4-6` by default; `claude-opus-4-7` for scenario paths).
3. Dispatches `tool_use` blocks to typed handlers in `service/tools/__init__.py`.
4. Collects `tool_result` responses and continues until `end_turn` or the tool-call cap.

## Invariants

### No prose-derived numbers
Every number in the final output (predicted draw numbers, confidence) **must** be
traceable to a tool invocation. Claude is instructed to:
- Call `get_next_draw_distribution` to obtain the probability vector.
- Call `materialize_suggestion` to obtain the 15-number recommendation.
- Never invent numbers from memory or reasoning alone.

The post-response validator (`_validate_response`) enforces:
- `confidence` must be present (KeyError → rejection).
- `confidence` must satisfy `0 < confidence < 1` (inclusive bounds rejected).
- `numbers` must be a list of exactly 15 values.

### Tool-call cap
`MAX_TOOL_CALLS = 20`. If the cap is reached, the loop exits and returns
whatever partial result is available. The API signals `tool_call_cap_reached`
in the error details.

### Calibration gate
If `CalibrationStatus.is_stale` is `True`, `get_next_draw_distribution` returns
`calibrated: false` in its result dict. The API layer must refuse to surface
play-surface suggestions when `calibrated: false`.

## Available Tools

| Tool | Input | Purpose |
|---|---|---|
| `get_dataset_provenance` | — | Dataset hash, date range, record count |
| `get_frequency` | `window` | Per-number draw frequency |
| `get_gap_statistics` | — | Hot/cold gap analysis |
| `get_cooccurrence` | `arity`, `top_k` | Top-K co-occurring combinations |
| `get_structural_distributions` | — | Sum, even/odd, quintile histograms |
| `get_pi_alignment` | `rule`, `target` | PI-alignment score + explanation |
| `get_signal_correlation` | `signal`, `metric`, `lag` | External signal correlation |
| `get_next_draw_distribution` | `baseline_weight`, `learned_weight` | Probability vector + distribution_id |
| `materialize_suggestion` | `distribution_id`, `top_k` | Concrete 15-number suggestion |
| `advance_scenario_step` | `state_id` | One step of a scenario path |

## Provenance Attachment

Every response includes a `provenance` dict:
```json
{
  "dataset_hash": "<sha256 prefix>",
  "model_versions": [{"name": "...", "version": "..."}],
  "agent_prompt_hash": "<sha256[:16] of system prompt>",
  "tool_trace": [...],
  "computed_at": "<ISO datetime>"
}
```

## Token Tracking

After every LLM API call, input/output token counts are forwarded to
`service/token_counters.py`. Cumulative totals are exposed on `GET /v1/ready`
under the `token_usage` check entry.

## Model Selection

| Use case | Model |
|---|---|
| Single next-draw prediction | `claude-sonnet-4-6` (DEFAULT_MODEL) |
| Scenario path | `claude-opus-4-7` (HEAVY_MODEL) |
| Cheap subtasks | `claude-haiku-4-5-20251001` (CHEAP_MODEL) |
