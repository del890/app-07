"""Typed tool handlers for the prediction agent (§8).

Each tool corresponds to one JSON-Schema ``tool`` definition that Claude can
invoke via its tool-use API. Inputs are validated by Pydantic models; outputs
are serialisable dicts that Claude sees as ``tool_result`` content.

Tool surface (design.md §4):

  get_dataset_provenance()
  get_frequency(window)
  get_gap_statistics()
  get_cooccurrence(arity, top_k)
  get_structural_distributions()
  get_pi_alignment(rule, target)
  get_signal_correlation(signal, metric, lag)
  get_next_draw_distribution()
  materialize_suggestion(top_k)
  advance_scenario_step(state_id)

All handlers return plain dicts (JSON-serialisable) so they can be forwarded
directly as ``tool_result.content`` to Claude.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from service.statistics.base import WindowSelection
from service.engine import (
    NUMBER_COUNT,
    CalibrationStatus,
    NextDrawDistribution,
    compute_next_draw_distribution,
    get_calibration_status,
)
from service.statistics import (
    ARITY_MAX,
    ARITY_MIN,
    TOP_K_MAX,
    compute_cooccurrence,
    compute_frequency,
    compute_gaps,
    compute_order,
    compute_pi_alignment,
    compute_structural,
)

# ---------------------------------------------------------------------------
# Tool input models — these define the JSON Schema the agent sees.
# ---------------------------------------------------------------------------


class GetDatasetProvenanceInput(BaseModel):
    """No parameters — returns dataset provenance."""


class GetFrequencyInput(BaseModel):
    """Frequency of each number in the dataset or a rolling window."""

    window: int | Literal["full"] = Field(
        default="full",
        description=(
            "Number of most-recent draws to include, or 'full' for the entire dataset."
        ),
    )


class GetGapStatisticsInput(BaseModel):
    """Gap (consecutive-absence) statistics for every number."""


class GetCooccurrenceInput(BaseModel):
    """Top-K co-occurring number combinations at a given arity."""

    arity: int = Field(
        default=2,
        ge=ARITY_MIN,
        le=ARITY_MAX,
        description="Size of each combination (2 = pairs, 3 = triples, 4 = quads).",
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=TOP_K_MAX,
        description="Number of top combinations to return.",
    )


class GetStructuralDistributionsInput(BaseModel):
    """Structural statistics (sum, even/odd, quintiles, min/max) over the dataset."""


class GetPiAlignmentInput(BaseModel):
    """PI-alignment analysis using a specific rule catalog entry."""

    rule: str = Field(
        description=(
            "Rule name from the PI rule catalog. "
            "Call this tool without a rule to list available rules."
        )
    )
    target: int | None = Field(
        default=None,
        description=(
            "Draw index (0-based) to score; if omitted, scores the entire dataset average."
        ),
    )


class GetSignalCorrelationInput(BaseModel):
    """Correlation between a named external signal and a draw metric."""

    signal: str = Field(description="Signal name as registered in the signal registry.")
    metric: str = Field(
        description=(
            "Draw metric to correlate against. "
            "Options: 'sum', 'even_count', 'mean_gap', 'frequency_<number>'."
        )
    )
    lag: int = Field(
        default=0,
        ge=0,
        le=52,
        description="Draw-lag (0 = same-draw alignment, 1 = predict one draw ahead, etc.).",
    )


class GetNextDrawDistributionInput(BaseModel):
    """Compute the ensemble next-draw probability distribution."""

    baseline_weight: float = Field(
        default=0.4, ge=0.0, description="Relative weight for the baseline model."
    )
    learned_weight: float = Field(
        default=0.6, ge=0.0, description="Relative weight for the learned GBM model."
    )


class MaterializeSuggestionInput(BaseModel):
    """Convert a pre-computed distribution into a concrete 15-number suggestion."""

    distribution_id: str = Field(
        description="ID returned by a previous get_next_draw_distribution call."
    )
    k: int = Field(
        default=15,
        ge=15,
        le=15,
        description="How many numbers to suggest (must be 15, the game rule).",
    )


class AdvanceScenarioStepInput(BaseModel):
    """Advance a scenario path by one draw step."""

    state_id: str = Field(
        description=(
            "State id returned by a previous advance_scenario_step call, "
            "or 'initial' to start a new path."
        )
    )
    horizon: int = Field(
        default=1,
        ge=1,
        le=20,
        description="Total desired path length used for monotonic confidence decay.",
    )
    step: int = Field(
        default=1,
        ge=1,
        description="Current step index (1-based) within the horizon.",
    )


# ---------------------------------------------------------------------------
# Tool schema generation
# ---------------------------------------------------------------------------

_TOOL_MODELS: dict[str, type[BaseModel]] = {
    "get_dataset_provenance": GetDatasetProvenanceInput,
    "get_frequency": GetFrequencyInput,
    "get_gap_statistics": GetGapStatisticsInput,
    "get_cooccurrence": GetCooccurrenceInput,
    "get_structural_distributions": GetStructuralDistributionsInput,
    "get_pi_alignment": GetPiAlignmentInput,
    "get_signal_correlation": GetSignalCorrelationInput,
    "get_next_draw_distribution": GetNextDrawDistributionInput,
    "materialize_suggestion": MaterializeSuggestionInput,
    "advance_scenario_step": AdvanceScenarioStepInput,
}

_TOOL_DESCRIPTIONS: dict[str, str] = {
    "get_dataset_provenance": (
        "Return the dataset provenance: record count, earliest/latest draw dates, "
        "source path, and content hash (SHA-256). Always call this first to anchor "
        "provenance in your response."
    ),
    "get_frequency": (
        "Return per-number frequency statistics. 'full' window uses all historical draws; "
        "an integer window uses only the N most-recent draws."
    ),
    "get_gap_statistics": (
        "Return gap (consecutive absence) statistics for each number 1–25, including "
        "current gap, mean gap, max gap, and hot/cold classification."
    ),
    "get_cooccurrence": (
        "Return the top-K most frequently co-occurring number sets at the given arity. "
        "Arity 2 = pairs, 3 = triples, 4 = quads."
    ),
    "get_structural_distributions": (
        "Return structural distribution statistics: draw sum histogram, even/odd counts, "
        "per-quintile number counts, and min/max statistics."
    ),
    "get_pi_alignment": (
        "Score a draw or the dataset average using one of the PI alignment rules. "
        "Omit 'target' to get the dataset-wide average score."
    ),
    "get_signal_correlation": (
        "Compute Spearman correlation between a named external signal and a draw metric. "
        "Returns effect size, p-value, sample size, and significance flag."
    ),
    "get_next_draw_distribution": (
        "Compute the ensemble next-draw probability distribution (25-length vector, "
        "sum = 15). Returns a distribution_id you must pass to materialize_suggestion."
    ),
    "materialize_suggestion": (
        "Convert a distribution into a concrete 15-number suggestion set. "
        "Selects numbers proportional to probability with diversity jitter."
    ),
    "advance_scenario_step": (
        "Advance a scenario path by one draw step. Each step conditions on the path so "
        "far and returns a predicted draw with a step-level confidence. "
        "Path confidence is monotonically non-increasing with horizon."
    ),
}


def build_tool_definitions() -> list[dict[str, Any]]:
    """Emit Anthropic-compatible JSON-Schema tool definitions from Pydantic models."""
    tools = []
    for name, model in _TOOL_MODELS.items():
        schema = model.model_json_schema()
        # Remove Pydantic's $defs / $schema / title noise that Claude doesn't need.
        schema.pop("$defs", None)
        schema.pop("$schema", None)
        schema.pop("title", None)
        tools.append(
            {
                "name": name,
                "description": _TOOL_DESCRIPTIONS.get(name, ""),
                "input_schema": schema,
            }
        )
    return tools


# ---------------------------------------------------------------------------
# In-process distribution cache (keyed by id)
# ---------------------------------------------------------------------------

_distribution_cache: dict[str, NextDrawDistribution] = {}


def _store_distribution(dist: NextDrawDistribution) -> str:
    did = str(uuid.uuid4())
    _distribution_cache[did] = dist
    return did


def get_distribution(did: str) -> NextDrawDistribution | None:
    return _distribution_cache.get(did)


def clear_distribution_cache() -> None:
    _distribution_cache.clear()


# ---------------------------------------------------------------------------
# Scenario path state (keyed by state_id)
# ---------------------------------------------------------------------------

_scenario_states: dict[str, dict[str, Any]] = {}


def _store_scenario_state(state: dict[str, Any]) -> str:
    sid = str(uuid.uuid4())
    _scenario_states[sid] = state
    return sid


def _get_scenario_state(sid: str) -> dict[str, Any] | None:
    return _scenario_states.get(sid)


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------


class ToolDispatcher:
    """Route tool calls to their handler functions, given a loaded DrawHistory."""

    def __init__(self, history: Any) -> None:  # DrawHistory
        self._history = history

    def dispatch(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Validate input, call the handler, return the result dict."""
        handler = _HANDLERS.get(tool_name)
        if handler is None:
            return {"error": f"Unknown tool: {tool_name}"}
        model_cls = _TOOL_MODELS.get(tool_name)
        if model_cls is None:
            return {"error": f"No input model for: {tool_name}"}
        try:
            validated = model_cls.model_validate(tool_input)
        except Exception as exc:
            return {"error": f"Invalid tool input: {exc}"}
        try:
            return handler(self._history, validated)
        except Exception as exc:
            return {"error": f"Tool execution failed: {exc}"}


# ---------------------------------------------------------------------------
# Individual tool handlers
# ---------------------------------------------------------------------------


def _handle_get_dataset_provenance(history: Any, _: GetDatasetProvenanceInput) -> dict:
    p = history.provenance
    return {
        "record_count": p.total_draws,
        "earliest_date": p.first_date.isoformat(),
        "latest_date": p.last_date.isoformat(),
        "source_path": str(p.source_path),
        "content_hash": p.content_hash,
    }


def _handle_get_frequency(history: Any, inp: GetFrequencyInput) -> dict:
    if inp.window == "full":
        window_sel: WindowSelection | None = None
    else:
        window_sel = WindowSelection(kind="last_n", n=int(inp.window))
    result = compute_frequency(history, window=window_sel)
    return {
        "window": result.meta.window,
        "dataset_hash": result.meta.dataset_hash,
        "computed_at": result.meta.computed_at.isoformat(),
        "frequencies": [
            {
                "number": f.number,
                "count": f.count,
                "share": float(f.share),
            }
            for f in result.frequencies
        ],
    }


def _handle_get_gap_statistics(history: Any, _: GetGapStatisticsInput) -> dict:
    result = compute_gaps(history)
    return {
        "dataset_hash": result.meta.dataset_hash,
        "computed_at": result.meta.computed_at.isoformat(),
        "hot_cold_threshold": result.threshold.model_dump(),
        "gaps": [
            {
                "number": g.number,
                "current_gap": g.current_gap,
                "mean_gap": g.mean_gap,
                "max_gap": g.max_gap,
                "classification": g.classification,
            }
            for g in result.gaps
        ],
    }


def _handle_get_cooccurrence(history: Any, inp: GetCooccurrenceInput) -> dict:
    result = compute_cooccurrence(history, arity=inp.arity, top_k=inp.top_k)
    return {
        "dataset_hash": result.meta.dataset_hash,
        "computed_at": result.meta.computed_at.isoformat(),
        "arity": inp.arity,
        "top_k": inp.top_k,
        "combinations": [
            {"numbers": list(c.numbers), "count": c.count}
            for c in result.combinations
        ],
    }


def _handle_get_structural_distributions(
    history: Any, _: GetStructuralDistributionsInput
) -> dict:
    result = compute_structural(history)
    return {
        "dataset_hash": result.meta.dataset_hash,
        "computed_at": result.meta.computed_at.isoformat(),
        "sum_min": result.sum_min,
        "sum_max": result.sum_max,
        "sum_histogram": [{"value": b.value, "count": b.count} for b in result.sum_histogram],
        "even_count_histogram": [{"value": b.value, "count": b.count} for b in result.even_count_histogram],
        "quintile_histogram": [{"value": b.value, "count": b.count} for b in result.quintile_histogram],
    }


def _handle_get_pi_alignment(history: Any, inp: GetPiAlignmentInput) -> dict:
    from service.statistics import RULES

    if inp.rule not in RULES:
        available = list(RULES.keys())
        return {
            "error": f"Unknown rule '{inp.rule}'. Available: {available}",
            "available_rules": available,
        }
    result = compute_pi_alignment(history, rule=inp.rule, target_index=inp.target)
    return {
        "dataset_hash": result.meta.dataset_hash,
        "computed_at": result.meta.computed_at.isoformat(),
        "rule": result.rule,
        "score": result.score,
        "explanation": result.explanation,
        "target": inp.target,
    }


def _handle_get_signal_correlation(
    history: Any, inp: GetSignalCorrelationInput
) -> dict:
    from service.correlation.registry import get_signal
    from service.correlation.compute import compute_single_correlation

    signal = get_signal(inp.signal)
    if signal is None:
        return {"error": f"Signal '{inp.signal}' not found in registry."}
    try:
        result = compute_single_correlation(history, signal, inp.metric, lag=inp.lag)
    except Exception as exc:
        return {"error": str(exc)}
    return {
        "signal": inp.signal,
        "metric": inp.metric,
        "lag": inp.lag,
        "rho": result.rho,
        "p_value": result.p_value,
        "effect_size": result.effect_size,
        "sample_size": result.sample_size,
        "test_used": result.test_used,
        "under_powered": result.under_powered,
        "significant": result.significant,
        "artifact_type": result.artifact_type,
        "disclaimer": result.disclaimer,
    }


def _handle_get_next_draw_distribution(
    history: Any, inp: GetNextDrawDistributionInput
) -> dict:
    dist = compute_next_draw_distribution(
        history,
        baseline_weight=inp.baseline_weight,
        learned_weight=inp.learned_weight,
    )
    did = _store_distribution(dist)
    cal_status: CalibrationStatus = get_calibration_status()
    return {
        "distribution_id": did,
        "calibrated": not cal_status.is_stale,
        "dataset_hash": dist.dataset_hash,
        "model_versions": [
            {"name": mv.name, "version": mv.version} for mv in dist.model_versions
        ],
        "ensemble_weights": dist.ensemble_weights,
        "probabilities": [
            {"number": p.number, "probability": p.probability}
            for p in dist.probabilities
        ],
        "computed_at": dist.computed_at.isoformat(),
    }


def _handle_materialize_suggestion(history: Any, inp: MaterializeSuggestionInput) -> dict:
    import random

    dist = get_distribution(inp.distribution_id)
    if dist is None:
        return {
            "error": f"Distribution '{inp.distribution_id}' not found. "
            "Call get_next_draw_distribution first."
        }
    cal_status = get_calibration_status()

    # Select 15 numbers weighted by probability (without replacement).
    numbers = [p.number for p in dist.probabilities]
    weights = [max(1e-9, p.probability) for p in dist.probabilities]
    # Weighted sampling without replacement via sequential draw.
    rng = random.Random()  # fresh RNG for diversity
    selected: list[int] = []
    remaining_nums = list(numbers)
    remaining_weights = list(weights)
    for _ in range(15):
        total = sum(remaining_weights)
        r = rng.uniform(0, total)
        cumulative = 0.0
        for i, w in enumerate(remaining_weights):
            cumulative += w
            if r <= cumulative:
                selected.append(remaining_nums[i])
                remaining_nums.pop(i)
                remaining_weights.pop(i)
                break
    selected.sort()

    # Raw confidence = mean probability of selected numbers (sum / 15).
    raw_confidence = sum(
        p.probability for p in dist.probabilities if p.number in selected
    ) / 15.0
    # Clamp strictly away from 0 and 1.
    confidence = max(1e-6, min(1.0 - 1e-6, raw_confidence))

    return {
        "numbers": selected,
        "confidence": confidence,
        "calibrated": not cal_status.is_stale,
        "distribution_id": inp.distribution_id,
        "dataset_hash": dist.dataset_hash,
        "model_versions": [
            {"name": mv.name, "version": mv.version} for mv in dist.model_versions
        ],
        "disclaimer": (
            "This suggestion is generated for research and entertainment purposes only. "
            "It is not a prediction of future lottery outcomes. "
            "No lottery outcome can be reliably predicted."
        ),
    }


def _handle_advance_scenario_step(history: Any, inp: AdvanceScenarioStepInput) -> dict:
    """Advance a scenario path by one step.

    Each step conditions on the evolving state (draw history + prior predicted draws)
    to produce the next predicted draw. Path confidence decays monotonically with
    step so that longer paths are never more confident than shorter prefixes.
    Confidence at step k = `base_confidence * (decay_factor ** (k - 1))`.
    """
    # Retrieve or initialise the scenario state.
    if inp.state_id == "initial":
        prior_state: dict[str, Any] = {
            "draws": [],
            "base_confidence": None,
            "dataset_hash": history.provenance.content_hash,
        }
    else:
        prior_state = _get_scenario_state(inp.state_id) or {}
        if not prior_state:
            return {"error": f"State '{inp.state_id}' not found. Use 'initial' to start."}

    # Generate the next-draw distribution conditioned on the extended history.
    dist = compute_next_draw_distribution(history)
    did = _store_distribution(dist)

    # Materialize the suggested draw using the distribution.
    mat_inp = MaterializeSuggestionInput(distribution_id=did)
    suggestion = _handle_materialize_suggestion(history, mat_inp)
    if "error" in suggestion:
        return suggestion

    step_confidence = suggestion["confidence"]
    base_confidence = prior_state.get("base_confidence")
    if base_confidence is None:
        base_confidence = step_confidence

    # Monotonic decay: confidence at step k ≤ confidence at step k-1.
    decay_factor = 0.95
    if inp.step > 1:
        step_confidence = min(step_confidence, base_confidence * (decay_factor ** (inp.step - 1)))
    step_confidence = max(1e-6, min(1.0 - 1e-6, step_confidence))

    cal_status = get_calibration_status()

    # Persist updated state.
    new_state: dict[str, Any] = {
        "draws": prior_state.get("draws", []) + [suggestion["numbers"]],
        "base_confidence": base_confidence,
        "dataset_hash": history.provenance.content_hash,
    }
    new_state_id = _store_scenario_state(new_state)

    return {
        "state_id": new_state_id,
        "step": inp.step,
        "horizon": inp.horizon,
        "predicted_numbers": suggestion["numbers"],
        "step_confidence": step_confidence,
        "path_draws_so_far": len(new_state["draws"]),
        "calibrated": not cal_status.is_stale,
        "dataset_hash": history.provenance.content_hash,
        "disclaimer": suggestion["disclaimer"],
    }


# Register handlers.
_HANDLERS: dict[str, Any] = {
    "get_dataset_provenance": _handle_get_dataset_provenance,
    "get_frequency": _handle_get_frequency,
    "get_gap_statistics": _handle_get_gap_statistics,
    "get_cooccurrence": _handle_get_cooccurrence,
    "get_structural_distributions": _handle_get_structural_distributions,
    "get_pi_alignment": _handle_get_pi_alignment,
    "get_signal_correlation": _handle_get_signal_correlation,
    "get_next_draw_distribution": _handle_get_next_draw_distribution,
    "materialize_suggestion": _handle_materialize_suggestion,
    "advance_scenario_step": _handle_advance_scenario_step,
}
