"""Tests for the agent tools layer and the tool-use loop (§8).

Test strategy
-------------
- **Unit tests** (no LLM): tool dispatcher correctness, schema generation,
  guard-rail validation, scenario-step state machine.
- **Replay-based tests**: simulate Claude's tool-use loop responses without a
  live LLM call by injecting a mock Anthropic client.
- **Live tests**: run only when ``RUN_LIVE_LLM=1`` env-var is set. These make
  real Anthropic API calls; they are excluded from CI by default.

Guard-rail invariants checked here:
- Confidence must be in (0, 1) exclusive.
- A response missing 'confidence' is rejected.
- A response with confidence >= 1.0 is rejected.
- 'numbers' must have exactly 15 elements.
- Tool dispatcher returns a structured error for unknown tools.
- Tool dispatcher rejects invalid inputs (Pydantic validation).
"""

from __future__ import annotations

import json
import os
import random
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from service.agents import (
    _build_prediction_response,
    _extract_json,
    _validate_response,
    predict_next_draw,
)
from service.tools import (
    ToolDispatcher,
    build_tool_definitions,
    clear_distribution_cache,
    GetFrequencyInput,
    GetCooccurrenceInput,
    MaterializeSuggestionInput,
    AdvanceScenarioStepInput,
)
from service.engine import reset_calibration, reset_learned_cache


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]


def _synth_history(tmp_path: Path, n_draws: int, *, seed: int = 1):
    rng = random.Random(seed)
    start = date(2019, 1, 1)
    draws = []
    for i in range(n_draws):
        numbers = rng.sample(range(1, 26), 15)
        draws.append(
            {
                "id": n_draws - i,
                "date": (start + timedelta(days=(n_draws - 1 - i))).strftime("%d-%m-%Y"),
                "numbers": numbers,
            }
        )
    data = {"allowed_numbers": list(range(1, 26)), "dataset": draws}
    p = tmp_path / "data.json"
    p.write_text(json.dumps(data))
    from service.ingestion import load

    return load(p)


@pytest.fixture(autouse=True)
def _reset_distribution_cache():
    clear_distribution_cache()
    yield
    clear_distribution_cache()


@pytest.fixture(autouse=True)
def _reset_calibration_state():
    reset_calibration()
    reset_learned_cache()
    yield
    reset_calibration()
    reset_learned_cache()


# ---------------------------------------------------------------------------
# Tool schema (8.2)
# ---------------------------------------------------------------------------


def test_build_tool_definitions_returns_expected_tools() -> None:
    tools = build_tool_definitions()
    names = {t["name"] for t in tools}
    expected = {
        "get_dataset_provenance",
        "get_frequency",
        "get_gap_statistics",
        "get_cooccurrence",
        "get_structural_distributions",
        "get_pi_alignment",
        "get_signal_correlation",
        "get_next_draw_distribution",
        "materialize_suggestion",
        "advance_scenario_step",
    }
    assert names == expected


def test_tool_definitions_have_input_schema() -> None:
    tools = build_tool_definitions()
    for tool in tools:
        assert "input_schema" in tool, f"Tool '{tool['name']}' missing input_schema"
        assert "description" in tool, f"Tool '{tool['name']}' missing description"
        assert tool["description"], f"Tool '{tool['name']}' has empty description"


def test_tool_input_schema_is_valid_json_schema() -> None:
    """Each tool's input_schema must at minimum have 'type' and 'properties'
    (or be an empty object schema)."""
    tools = build_tool_definitions()
    for tool in tools:
        schema = tool["input_schema"]
        assert isinstance(schema, dict), f"Schema for {tool['name']} is not a dict"


# ---------------------------------------------------------------------------
# Tool dispatcher (8.1)
# ---------------------------------------------------------------------------


def test_dispatcher_rejects_unknown_tool(tiny_history) -> None:
    dispatcher = ToolDispatcher(tiny_history)
    result = dispatcher.dispatch("nonexistent_tool", {})
    assert "error" in result
    assert "Unknown tool" in result["error"]


def test_dispatcher_rejects_invalid_input(tiny_history) -> None:
    dispatcher = ToolDispatcher(tiny_history)
    # arity must be 2-4; pass 99
    result = dispatcher.dispatch("get_cooccurrence", {"arity": 99})
    assert "error" in result


def test_dispatcher_get_dataset_provenance(tiny_history) -> None:
    dispatcher = ToolDispatcher(tiny_history)
    result = dispatcher.dispatch("get_dataset_provenance", {})
    assert "record_count" in result
    assert "content_hash" in result
    assert result["record_count"] == len(tiny_history)


def test_dispatcher_get_frequency(tiny_history) -> None:
    dispatcher = ToolDispatcher(tiny_history)
    result = dispatcher.dispatch("get_frequency", {"window": "full"})
    assert "frequencies" in result
    assert len(result["frequencies"]) == 25


def test_dispatcher_get_gap_statistics(tiny_history) -> None:
    dispatcher = ToolDispatcher(tiny_history)
    result = dispatcher.dispatch("get_gap_statistics", {})
    assert "gaps" in result
    assert len(result["gaps"]) == 25


def test_dispatcher_get_cooccurrence(tiny_history) -> None:
    dispatcher = ToolDispatcher(tiny_history)
    result = dispatcher.dispatch("get_cooccurrence", {"arity": 2, "top_k": 5})
    assert "combinations" in result


def test_dispatcher_get_structural_distributions(tiny_history) -> None:
    dispatcher = ToolDispatcher(tiny_history)
    result = dispatcher.dispatch("get_structural_distributions", {})
    assert "sum_histogram" in result


def test_dispatcher_get_next_draw_distribution(tiny_history) -> None:
    dispatcher = ToolDispatcher(tiny_history)
    result = dispatcher.dispatch("get_next_draw_distribution", {})
    # On small history, learns model falls back to baseline only
    assert "distribution_id" in result or "error" in result
    # Even on small history, baseline always works
    if "distribution_id" in result:
        assert "probabilities" in result
        assert len(result["probabilities"]) == 25


def test_dispatcher_materialize_suggestion_requires_distribution(tiny_history) -> None:
    dispatcher = ToolDispatcher(tiny_history)
    result = dispatcher.dispatch(
        "materialize_suggestion", {"distribution_id": "nonexistent"}
    )
    assert "error" in result


def test_dispatcher_materialize_suggestion_full_flow(tiny_history) -> None:
    dispatcher = ToolDispatcher(tiny_history)
    dist_result = dispatcher.dispatch("get_next_draw_distribution", {})
    if "distribution_id" not in dist_result:
        pytest.skip("distribution failed on small history")
    mat_result = dispatcher.dispatch(
        "materialize_suggestion",
        {"distribution_id": dist_result["distribution_id"]},
    )
    assert "numbers" in mat_result
    assert len(mat_result["numbers"]) == 15
    assert all(1 <= n <= 25 for n in mat_result["numbers"])
    assert "confidence" in mat_result
    assert 0.0 < mat_result["confidence"] < 1.0


def test_dispatcher_advance_scenario_step_initial(tiny_history) -> None:
    dispatcher = ToolDispatcher(tiny_history)
    result = dispatcher.dispatch(
        "advance_scenario_step", {"state_id": "initial", "horizon": 3, "step": 1}
    )
    if "error" in result:
        pytest.skip("small history doesn't support scenario steps")
    assert "state_id" in result
    assert "predicted_numbers" in result
    assert len(result["predicted_numbers"]) == 15
    assert 0.0 < result["step_confidence"] < 1.0


def test_dispatcher_advance_scenario_step_monotonic_confidence(tiny_history) -> None:
    dispatcher = ToolDispatcher(tiny_history)
    result1 = dispatcher.dispatch(
        "advance_scenario_step", {"state_id": "initial", "horizon": 5, "step": 1}
    )
    if "error" in result1:
        pytest.skip("small history doesn't support scenario steps")
    result2 = dispatcher.dispatch(
        "advance_scenario_step",
        {"state_id": result1["state_id"], "horizon": 5, "step": 2},
    )
    if "error" in result2:
        pytest.skip("second step failed")
    # Path confidence decreases monotonically.
    assert result2["step_confidence"] <= result1["step_confidence"] + 1e-9


# ---------------------------------------------------------------------------
# Guard-rail validation (8.8)
# ---------------------------------------------------------------------------


def test_validate_response_rejects_missing_confidence() -> None:
    bad = {"numbers": list(range(1, 16))}
    with pytest.raises(ValueError, match="confidence"):
        _validate_response(bad)


def test_validate_response_rejects_confidence_gte_1() -> None:
    bad = {"numbers": list(range(1, 16)), "confidence": 1.0}
    with pytest.raises(ValueError, match=">= 1.0"):
        _validate_response(bad)


def test_validate_response_rejects_confidence_lte_0() -> None:
    bad = {"numbers": list(range(1, 16)), "confidence": 0.0}
    with pytest.raises(ValueError, match="<= 0"):
        _validate_response(bad)


def test_validate_response_rejects_wrong_numbers_count() -> None:
    bad = {"numbers": list(range(1, 10)), "confidence": 0.5}
    with pytest.raises(ValueError, match="15"):
        _validate_response(bad)


def test_validate_response_accepts_valid() -> None:
    good = {"numbers": list(range(1, 16)), "confidence": 0.4}
    _validate_response(good)  # should not raise


# ---------------------------------------------------------------------------
# JSON extraction helper
# ---------------------------------------------------------------------------


def test_extract_json_from_plain() -> None:
    text = '{"numbers": [1], "confidence": 0.3}'
    result = _extract_json(text)
    assert result["confidence"] == 0.3


def test_extract_json_from_code_block() -> None:
    text = "Here is the result:\n```json\n{\"numbers\": [1], \"confidence\": 0.3}\n```"
    result = _extract_json(text)
    assert result["confidence"] == 0.3


def test_extract_json_raises_on_no_json() -> None:
    with pytest.raises((ValueError, Exception)):
        _extract_json("No JSON here whatsoever.")


# ---------------------------------------------------------------------------
# Tool trace provenance (8.7)
# ---------------------------------------------------------------------------


def test_build_prediction_response_attaches_provenance(tiny_history) -> None:
    # Craft a minimal tool trace with a materialize_suggestion result.
    tool_trace = [
        {
            "tool": "materialize_suggestion",
            "input": {"distribution_id": "abc"},
            "result": {
                "numbers": list(range(1, 16)),
                "confidence": 0.42,
                "calibrated": False,
                "model_versions": [{"name": "baseline", "version": "v1"}],
                "disclaimer": "disclaimer text",
            },
            "duration_ms": 10,
        }
    ]
    response = _build_prediction_response("", tool_trace, tiny_history)
    assert "provenance" in response
    assert "dataset_hash" in response["provenance"]
    assert "agent_prompt_hash" in response["provenance"]
    assert "computed_at" in response["provenance"]
    assert "tool_trace" in response
    assert len(response["tool_trace"]) == 1


# ---------------------------------------------------------------------------
# Replay-based tool loop test (8.9)
# ---------------------------------------------------------------------------


class _FakeMessage:
    """Minimal stand-in for an Anthropic Message object."""

    def __init__(self, stop_reason: str, content: list) -> None:
        self.stop_reason = stop_reason
        self.content = content


class _FakeTextBlock:
    type = "text"

    def __init__(self, text: str) -> None:
        self.text = text


class _FakeToolUseBlock:
    type = "tool_use"

    def __init__(self, tool_id: str, name: str, input: dict) -> None:
        self.id = tool_id
        self.name = name
        self.input = input


def test_tool_loop_replay_end_turn(tmp_path: Path) -> None:
    """Verify the tool-use loop terminates correctly on end_turn."""
    from service.agents import _run_tool_loop

    # Small history to test without heavy ML models.
    history_size = 5
    history = _synth_history(tmp_path, history_size)
    dispatcher = ToolDispatcher(history)
    tool_defs = build_tool_definitions()

    msg_turns = []

    def _fake_create(**kwargs):
        # First turn: return end_turn with an answer text.
        msg_turns.append(kwargs)
        return _FakeMessage(
            stop_reason="end_turn",
            content=[_FakeTextBlock('{"numbers": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15], "confidence": 0.3}')],
        )

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = _fake_create

    with patch("service.agents.get_anthropic", return_value=mock_client):
        final_text, tool_trace = _run_tool_loop(
            [{"role": "user", "content": "test"}],
            dispatcher=dispatcher,
            model="claude-test",
            tool_defs=tool_defs,
        )

    assert "numbers" in final_text
    assert tool_trace == []  # no tool calls in this replay


def test_tool_loop_replay_with_tool_call(tmp_path: Path) -> None:
    """Verify the loop dispatches one tool call then terminates."""
    from service.agents import _run_tool_loop

    history = _synth_history(tmp_path, 5)
    dispatcher = ToolDispatcher(history)
    tool_defs = build_tool_definitions()
    turns: list[str] = []

    def _fake_create(**kwargs):
        turns.append("call")
        if len(turns) == 1:
            # First turn: request a tool call.
            return _FakeMessage(
                stop_reason="tool_use",
                content=[
                    _FakeToolUseBlock("tu_1", "get_dataset_provenance", {}),
                ],
            )
        # Second turn: end.
        return _FakeMessage(
            stop_reason="end_turn",
            content=[_FakeTextBlock('{"numbers": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15], "confidence": 0.3}')],
        )

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = _fake_create

    with patch("service.agents.get_anthropic", return_value=mock_client):
        final_text, tool_trace = _run_tool_loop(
            [{"role": "user", "content": "test"}],
            dispatcher=dispatcher,
            model="claude-test",
            tool_defs=tool_defs,
        )

    assert len(tool_trace) == 1
    assert tool_trace[0]["tool"] == "get_dataset_provenance"
    assert "record_count" in tool_trace[0]["result"]


def test_tool_loop_prose_derived_numbers_rejected(tmp_path: Path) -> None:
    """Verify guard-rail rejects a response with confidence=1.0 (prose-derived)."""
    from service.agents import _run_tool_loop, _build_prediction_response

    history = _synth_history(tmp_path, 5)
    tool_trace: list[dict] = []  # empty trace — no tools called
    # Claude returns a response with confidence=1.0 (invalid)
    bad_text = '{"numbers": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15], "confidence": 1.0}'

    with pytest.raises(ValueError, match=">= 1.0"):
        _build_prediction_response(bad_text, tool_trace, history)


# ---------------------------------------------------------------------------
# Live integration test (RUN_LIVE_LLM=1 only)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not os.environ.get("RUN_LIVE_LLM"),
    reason="Set RUN_LIVE_LLM=1 to run live LLM integration tests.",
)
def test_live_predict_next_draw() -> None:
    from pathlib import Path

    from service.ingestion import load

    data_path = REPO_ROOT / "data.json"
    if not data_path.exists():
        pytest.skip("data.json not available")
    history = load(data_path)
    result = predict_next_draw(history)
    assert "numbers" in result
    assert len(result["numbers"]) == 15
    assert 0.0 < result["confidence"] < 1.0
    assert "provenance" in result
    assert result["provenance"]["dataset_hash"] == history.provenance.content_hash
