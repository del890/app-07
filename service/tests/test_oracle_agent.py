"""Unit tests for the dream-oracle agent."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from service.oracle.agent import _build_oracle_response, _validate_tool_trace_order
from service.oracle.tools import (
    OracleToolDispatcher,
    _handle_extract_dream_signals,
    _handle_oracle_materialize,
    _oracle_distributions,
    clear_oracle_distribution_cache,
    ExtractDreamSignalsInput,
    OracleMaterializeSuggestionInput,
)
from service.oracle.models import ExtractedSymbol


@pytest.fixture(autouse=True)
def _clear_oracle_cache() -> None:
    clear_oracle_distribution_cache()
    yield
    clear_oracle_distribution_cache()


# ---------------------------------------------------------------------------
# Tool trace order validation
# ---------------------------------------------------------------------------


def test_validate_order_ok() -> None:
    trace = [
        {"tool": "extract_dream_signals"},
        {"tool": "materialize_suggestion"},
    ]
    _validate_tool_trace_order(trace)  # should not raise


def test_validate_order_materialize_without_extract_raises() -> None:
    trace = [{"tool": "materialize_suggestion"}]
    with pytest.raises(ValueError, match="extract_dream_signals"):
        _validate_tool_trace_order(trace)


def test_validate_order_materialize_before_extract_raises() -> None:
    trace = [
        {"tool": "materialize_suggestion"},
        {"tool": "extract_dream_signals"},
    ]
    with pytest.raises(ValueError, match="extract_dream_signals"):
        _validate_tool_trace_order(trace)


def test_validate_order_empty_trace_ok() -> None:
    _validate_tool_trace_order([])  # neither tool called — no violation


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------


def _make_symbols(n: int = 2) -> list[dict]:
    return [
        {"category": "element", "label": "water", "intensity": 0.8},
        {"category": "emotion", "label": "joy", "intensity": 0.6},
    ][:n]


def test_dispatcher_extract_dream_signals() -> None:
    dispatcher = OracleToolDispatcher()
    result = dispatcher.dispatch("extract_dream_signals", {"symbols": _make_symbols()})
    assert "distribution_id" in result
    assert "catalog_version" in result
    assert "symbols_applied" in result


def test_dispatcher_materialize_requires_prior_extract() -> None:
    dispatcher = OracleToolDispatcher()
    result = dispatcher.dispatch(
        "materialize_suggestion", {"distribution_id": "nonexistent-id"}
    )
    assert "error" in result


def test_dispatcher_full_flow_produces_15_numbers() -> None:
    dispatcher = OracleToolDispatcher()
    extract_result = dispatcher.dispatch(
        "extract_dream_signals", {"symbols": _make_symbols(2)}
    )
    dist_id = extract_result["distribution_id"]
    materialize_result = dispatcher.dispatch(
        "materialize_suggestion", {"distribution_id": dist_id}
    )
    assert "numbers" in materialize_result
    assert len(materialize_result["numbers"]) == 15
    assert all(1 <= n <= 25 for n in materialize_result["numbers"])
    assert len(set(materialize_result["numbers"])) == 15  # no duplicates


def test_dispatcher_unknown_tool_returns_error() -> None:
    dispatcher = OracleToolDispatcher()
    result = dispatcher.dispatch("nonexistent_tool", {})
    assert "error" in result


# ---------------------------------------------------------------------------
# Response builder
# ---------------------------------------------------------------------------


def _build_good_trace() -> tuple[list[dict], str]:
    """Return a minimal tool trace that passes all validations."""
    dispatcher = OracleToolDispatcher()
    extract_result = dispatcher.dispatch(
        "extract_dream_signals",
        {"symbols": [{"category": "element", "label": "fire", "intensity": 1.0}]},
    )
    dist_id = extract_result["distribution_id"]
    materialize_result = dispatcher.dispatch(
        "materialize_suggestion", {"distribution_id": dist_id}
    )
    numbers = materialize_result["numbers"]
    symbols = [{"category": "element", "label": "fire", "intensity": 1.0}]
    catalog_version = extract_result["catalog_version"]

    trace = [
        {"tool": "extract_dream_signals", "input": {"symbols": symbols}, "result": extract_result},
        {"tool": "materialize_suggestion", "input": {"distribution_id": dist_id}, "result": materialize_result},
    ]
    final_text = (
        f'{{"numbers": {numbers}, "explanation": "Fire symbol", '
        f'"symbols": {symbols}, "catalog_version": "{catalog_version}", '
        f'"artifact_type": "entertainment", "disclaimer": "Entertainment only."}}'
    )
    return trace, final_text


def test_build_oracle_response_artifact_type_is_entertainment() -> None:
    trace, final_text = _build_good_trace()
    result = _build_oracle_response(final_text, trace)
    assert result["artifact_type"] == "entertainment"


def test_build_oracle_response_has_15_numbers() -> None:
    trace, final_text = _build_good_trace()
    result = _build_oracle_response(final_text, trace)
    assert len(result["numbers"]) == 15


def test_build_oracle_response_fallback_from_trace() -> None:
    """If agent text has no JSON, numbers are still recovered from the trace."""
    trace, _ = _build_good_trace()
    result = _build_oracle_response("Some prose without JSON", trace)
    assert len(result["numbers"]) == 15
    assert result["artifact_type"] == "entertainment"


def test_build_oracle_response_raises_without_numbers() -> None:
    with pytest.raises(ValueError, match="15 numbers"):
        _build_oracle_response("{}", [])
