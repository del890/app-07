"""Tool definitions and dispatcher for the dream-oracle agent.

Tools exposed to the oracle agent:
  extract_dream_signals   — register extracted symbols; returns a distribution_id
  materialize_suggestion  — convert a distribution into 15 concrete numbers
"""

from __future__ import annotations

import logging
import random
import uuid
from typing import Any

from pydantic import BaseModel, Field

from service.oracle.bias import build_bias_vector
from service.oracle.catalog import CATALOG_VERSION, lookup
from service.oracle.models import ExtractedSymbol

logger = logging.getLogger(__name__)

_ORACLE_DISCLAIMER = (
    "Numbers are derived from symbolic mapping for entertainment only. "
    "No statistical or predictive basis. Jogue com responsabilidade."
)

# Per-process oracle distribution cache (maps distribution_id → bias_vector).
_oracle_distributions: dict[str, list[float]] = {}


# ---------------------------------------------------------------------------
# Tool input models
# ---------------------------------------------------------------------------


class ExtractDreamSignalsInput(BaseModel):
    """Symbols the agent identified from the dream description."""

    symbols: list[ExtractedSymbol] = Field(
        min_length=1,
        description="List of symbolic signals identified in the dream.",
    )


class OracleMaterializeSuggestionInput(BaseModel):
    """Materialize 15 numbers from an oracle distribution."""

    distribution_id: str = Field(
        description="ID returned by a previous extract_dream_signals call."
    )


_ORACLE_TOOL_MODELS: dict[str, type[BaseModel]] = {
    "extract_dream_signals": ExtractDreamSignalsInput,
    "materialize_suggestion": OracleMaterializeSuggestionInput,
}

_ORACLE_TOOL_DESCRIPTIONS: dict[str, str] = {
    "extract_dream_signals": (
        "Register the symbolic signals you identified in the dream. "
        "Each symbol has a category (element, color, emotion, archetype, count), "
        "a label (e.g. 'water', 'red', 'joy', 'falling', '7'), and an intensity in [0, 1]. "
        "Returns a distribution_id you must pass to materialize_suggestion."
    ),
    "materialize_suggestion": (
        "Convert the oracle distribution into exactly 15 concrete Lotofácil numbers. "
        "Pass the distribution_id returned by extract_dream_signals."
    ),
}


# ---------------------------------------------------------------------------
# Tool schema builder
# ---------------------------------------------------------------------------


def build_oracle_tool_definitions() -> list[dict[str, Any]]:
    """Emit Anthropic-compatible JSON-Schema tool definitions."""
    tools = []
    for name, model in _ORACLE_TOOL_MODELS.items():
        schema = model.model_json_schema()
        schema.pop("$defs", None)
        schema.pop("$schema", None)
        schema.pop("title", None)
        tools.append(
            {
                "name": name,
                "description": _ORACLE_TOOL_DESCRIPTIONS.get(name, ""),
                "input_schema": schema,
            }
        )
    return tools


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


def _handle_extract_dream_signals(inp: ExtractDreamSignalsInput) -> dict:
    bias_vector = build_bias_vector(inp.symbols)
    did = str(uuid.uuid4())
    _oracle_distributions[did] = bias_vector

    symbols_applied = []
    symbols_skipped = []
    for sym in inp.symbols:
        rule = lookup(sym.category, sym.label)
        if rule is None:
            symbols_skipped.append({"category": sym.category, "label": sym.label})
        else:
            symbols_applied.append(
                {
                    "category": sym.category,
                    "label": sym.label,
                    "intensity": sym.intensity,
                    "rationale": rule.rationale,
                    "numbers_boosted": rule.numbers,
                }
            )

    return {
        "distribution_id": did,
        "catalog_version": CATALOG_VERSION,
        "symbols_applied": symbols_applied,
        "symbols_skipped": symbols_skipped,
    }


def _handle_oracle_materialize(inp: OracleMaterializeSuggestionInput) -> dict:
    bias_vector = _oracle_distributions.get(inp.distribution_id)
    if bias_vector is None:
        return {
            "error": (
                f"Distribution '{inp.distribution_id}' not found. "
                "Call extract_dream_signals first."
            )
        }

    # Weighted sampling without replacement.
    numbers = list(range(1, 26))
    weights = [max(1e-9, w) for w in bias_vector]
    rng = random.Random()
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

    return {
        "numbers": selected,
        "distribution_id": inp.distribution_id,
        "disclaimer": _ORACLE_DISCLAIMER,
    }


def clear_oracle_distribution_cache() -> None:
    """Remove all cached oracle distributions. Used in tests."""
    _oracle_distributions.clear()


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


class OracleToolDispatcher:
    """Route oracle tool calls to their handlers."""

    def dispatch(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        model_cls = _ORACLE_TOOL_MODELS.get(tool_name)
        if model_cls is None:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            validated = model_cls.model_validate(tool_input)
        except Exception as exc:
            return {"error": f"Invalid tool input: {exc}"}
        try:
            if tool_name == "extract_dream_signals":
                return _handle_extract_dream_signals(validated)  # type: ignore[arg-type]
            elif tool_name == "materialize_suggestion":
                return _handle_oracle_materialize(validated)  # type: ignore[arg-type]
            else:
                return {"error": f"Unhandled tool: {tool_name}"}
        except Exception as exc:
            return {"error": f"Tool execution failed: {exc}"}
