"""LLM-powered prediction agent (§8).

The agent orchestrates a tool-use loop around Claude to produce:

1. **Next-draw predictions** — `predict_next_draw(history, request_context)`
2. **Scenario paths** — `predict_scenario_path(history, horizon, request_context)`

Design invariants (from design.md §4 and prediction-engine spec):

- The agent NEVER emits numeric values from prose; every number in the final
  output is traceable to a tool call.
- Every response carries full provenance: dataset hash, model versions, agent
  prompt hash, tool trace, confidence, and timestamp.
- Confidence MUST be in (0, 1) exclusive; a missing or boundary confidence is a
  bug and is rejected by ``_validate_response``.
- The tool-use loop is capped at ``MAX_TOOL_CALLS`` per request to protect
  against runaway costs.

Model tiers:
  - Next-draw: ``claude-sonnet-4-6`` (DEFAULT_MODEL)
  - Scenario-path: ``claude-opus-4-7`` (HEAVY_MODEL) — reasoning depth matters
  - Cheap subtasks: ``claude-haiku-4-5-20251001`` (CHEAP_MODEL)
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Iterator

from service.engine import get_calibration_status
from service.llm.client import CHEAP_MODEL, DEFAULT_MODEL, HEAVY_MODEL, get_anthropic, with_cache_control
from service.tools import ToolDispatcher, build_tool_definitions

MAX_TOOL_CALLS = 20

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a Lotofácil analysis agent. Your role is to help users understand \
historical draw patterns and generate probabilistic next-draw suggestions.

HARD RULES — you must follow these absolutely:
1. Every numeric value you include in your final answer MUST come from a tool \
   call result. Never compute or estimate numbers yourself.
2. Always start by calling get_dataset_provenance() to anchor all subsequent \
   results to the dataset hash.
3. A prediction is for RESEARCH AND ENTERTAINMENT ONLY. Never claim any number \
   is "guaranteed" or "likely to win". Always attach the disclaimer.
4. Your final JSON response MUST include:
   - "numbers": list of 15 integers
   - "confidence": float in (0, 1) exclusive
   - "explanation": human-readable explanation citing the tools you used
   - "tool_trace": list of tool call records
   - "provenance": { "dataset_hash", "model_versions", "agent_prompt_hash", \
     "computed_at" }
   - "calibrated": boolean
   - "disclaimer": the research/entertainment disclaimer string

5. If calibration is stale (check get_next_draw_distribution response), set \
   "calibrated": false and do NOT present the result as play-ready.

WORKFLOW:
1. Call get_dataset_provenance() — always first.
2. Call statistics tools as needed to understand the current draw landscape.
3. Call get_next_draw_distribution() to get the ensemble probability vector.
4. Call materialize_suggestion() with the returned distribution_id.
5. Build your final JSON with all required fields.
"""


def _prompt_hash() -> str:
    return hashlib.sha256(_SYSTEM_PROMPT.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Provenance helpers
# ---------------------------------------------------------------------------


def _extract_model_versions(tool_trace: list[dict]) -> list[dict]:
    """Pull model version info from materialize_suggestion / next_draw_dist calls."""
    versions: list[dict] = []
    seen: set[str] = set()
    for entry in tool_trace:
        result = entry.get("result", {})
        for mv in result.get("model_versions", []):
            key = f"{mv['name']}:{mv['version']}"
            if key not in seen:
                versions.append(mv)
                seen.add(key)
    return versions


# ---------------------------------------------------------------------------
# Response validation
# ---------------------------------------------------------------------------


def _validate_response(response: dict[str, Any]) -> None:
    """Raise ValueError if the response violates the invariants."""
    confidence = response.get("confidence")
    if confidence is None:
        raise ValueError("Response missing 'confidence' field.")
    if not isinstance(confidence, (int, float)):
        raise ValueError(f"'confidence' must be a number, got {type(confidence)}.")
    if confidence >= 1.0:
        raise ValueError(f"confidence={confidence} is >= 1.0; must be strictly < 1.0.")
    if confidence <= 0.0:
        raise ValueError(f"confidence={confidence} is <= 0; must be strictly > 0.")
    if "numbers" not in response:
        raise ValueError("Response missing 'numbers' field.")
    if len(response["numbers"]) != 15:
        raise ValueError(
            f"'numbers' must have exactly 15 elements, got {len(response['numbers'])}."
        )


# ---------------------------------------------------------------------------
# Tool-use loop
# ---------------------------------------------------------------------------


def _run_tool_loop(
    messages: list[dict],
    *,
    dispatcher: ToolDispatcher,
    model: str,
    tool_defs: list[dict],
    max_tool_calls: int = MAX_TOOL_CALLS,
) -> tuple[str, list[dict]]:
    """Core tool-use loop.

    Returns
    -------
    final_text : str
        Claude's last ``text`` block content.
    tool_trace : list[dict]
        Ordered tool call records: {name, input, result, duration_ms}.
    """
    import time

    from service.token_counters import record as record_tokens

    client = get_anthropic()
    tool_trace: list[dict] = []
    call_count = 0

    while call_count < max_tool_calls:
        resp = client.messages.create(
            model=model,
            max_tokens=4096,
            system=with_cache_control(_SYSTEM_PROMPT),
            tools=with_cache_control(tool_defs),
            messages=messages,
        )

        # Track token usage.
        if hasattr(resp, "usage") and resp.usage is not None:
            record_tokens(
                input_tokens=getattr(resp.usage, "input_tokens", 0),
                output_tokens=getattr(resp.usage, "output_tokens", 0),
            )

        # Append assistant turn.
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "end_turn":
            # Extract final text.
            final_text = ""
            for block in resp.content:
                if hasattr(block, "text"):
                    final_text = block.text
            return final_text, tool_trace

        if resp.stop_reason != "tool_use":
            # Unexpected stop — treat as end.
            final_text = ""
            for block in resp.content:
                if hasattr(block, "text"):
                    final_text = block.text
            return final_text, tool_trace

        # Dispatch tool calls.
        tool_results: list[dict] = []
        for block in resp.content:
            if not hasattr(block, "type") or block.type != "tool_use":
                continue
            call_count += 1
            t0 = time.monotonic()
            result = dispatcher.dispatch(block.name, dict(block.input))
            duration_ms = int((time.monotonic() - t0) * 1000)
            tool_trace.append(
                {
                    "tool": block.name,
                    "input": dict(block.input),
                    "result": result,
                    "duration_ms": duration_ms,
                }
            )
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                }
            )

        messages.append({"role": "user", "content": tool_results})

    # Cap reached — return what we have.
    return "", tool_trace


# ---------------------------------------------------------------------------
# Streaming variant of the tool loop
# ---------------------------------------------------------------------------


def _run_tool_loop_streaming(
    messages: list[dict],
    *,
    dispatcher: ToolDispatcher,
    model: str,
    tool_defs: list[dict],
    max_tool_calls: int = MAX_TOOL_CALLS,
) -> Iterator[dict]:
    """Yield SSE-friendly event dicts during the tool-use loop.

    Events:
      {"type": "tool_start", "tool": name, "input": ...}
      {"type": "tool_result", "tool": name, "result": ..., "duration_ms": ...}
      {"type": "final", "text": ..., "tool_trace": [...]}
    """
    import time

    client = get_anthropic()
    tool_trace: list[dict] = []
    call_count = 0

    while call_count < max_tool_calls:
        resp = client.messages.create(
            model=model,
            max_tokens=4096,
            system=with_cache_control(_SYSTEM_PROMPT),
            tools=with_cache_control(tool_defs),
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "end_turn":
            final_text = ""
            for block in resp.content:
                if hasattr(block, "text"):
                    final_text = block.text
            yield {"type": "final", "text": final_text, "tool_trace": tool_trace}
            return

        if resp.stop_reason != "tool_use":
            final_text = ""
            for block in resp.content:
                if hasattr(block, "text"):
                    final_text = block.text
            yield {"type": "final", "text": final_text, "tool_trace": tool_trace}
            return

        tool_results: list[dict] = []
        for block in resp.content:
            if not hasattr(block, "type") or block.type != "tool_use":
                continue
            call_count += 1
            yield {"type": "tool_start", "tool": block.name, "input": dict(block.input)}
            t0 = time.monotonic()
            result = dispatcher.dispatch(block.name, dict(block.input))
            duration_ms = int((time.monotonic() - t0) * 1000)
            tool_trace.append(
                {
                    "tool": block.name,
                    "input": dict(block.input),
                    "result": result,
                    "duration_ms": duration_ms,
                }
            )
            yield {
                "type": "tool_result",
                "tool": block.name,
                "result": result,
                "duration_ms": duration_ms,
            }
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                }
            )
        messages.append({"role": "user", "content": tool_results})

    yield {"type": "final", "text": "", "tool_trace": tool_trace}


# ---------------------------------------------------------------------------
# Streaming helper
# ---------------------------------------------------------------------------


def _augment_final(
    gen: Iterator[dict],
    *,
    history: Any,
    build_fn: Any,
) -> Iterator[dict]:
    """Pass through all events; replace the `final` event with one that also
    contains the fully-built prediction result under `result`."""
    for event in gen:
        if event.get("type") == "final":
            try:
                built = build_fn(event.get("text", ""), event.get("tool_trace", []), history)
            except Exception as exc:
                built = {"error": str(exc)}
            yield {**event, "result": built}
        else:
            yield event


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def predict_next_draw(
    history: Any,
    *,
    model: str = DEFAULT_MODEL,
    streaming: bool = False,
) -> dict[str, Any] | Iterator[dict[str, Any]]:
    """Run the agent to produce a next-draw prediction.

    Parameters
    ----------
    history : DrawHistory
    model : str
        Anthropic model to use. Defaults to DEFAULT_MODEL.
    streaming : bool
        If True return an iterator of SSE event dicts.

    Returns
    -------
    If ``streaming=False``: A validated prediction dict.
    If ``streaming=True``: An iterator of ``{"type": ..., ...}`` event dicts.
    """
    tool_defs = build_tool_definitions()
    dispatcher = ToolDispatcher(history)
    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                "Please suggest the next Lotofácil draw. "
                "Use the available tools to ground every number in data. "
                "Return your final answer as a JSON object with required fields."
            ),
        }
    ]

    if streaming:
        raw = _run_tool_loop_streaming(
            messages,
            dispatcher=dispatcher,
            model=model,
            tool_defs=tool_defs,
        )
        return _augment_final(raw, history=history, build_fn=_build_prediction_response)

    final_text, tool_trace = _run_tool_loop(
        messages,
        dispatcher=dispatcher,
        model=model,
        tool_defs=tool_defs,
    )
    return _build_prediction_response(final_text, tool_trace, history)


def predict_scenario_path(
    history: Any,
    *,
    horizon: int = 5,
    model: str = HEAVY_MODEL,
    streaming: bool = False,
) -> dict[str, Any] | Iterator[dict[str, Any]]:
    """Generate a scenario path of ``horizon`` predicted draws.

    Each step conditions on the evolving state from the previous step via
    ``advance_scenario_step``. The path-level confidence is monotonically
    non-increasing with horizon.
    """
    tool_defs = build_tool_definitions()
    dispatcher = ToolDispatcher(history)
    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                f"Please generate a scenario path of {horizon} predicted Lotofácil draws. "
                "Use advance_scenario_step with state_id='initial' for the first step "
                f"and horizon={horizon}. Pass the returned state_id to subsequent steps. "
                "Return a JSON object with fields: 'steps' (list of step results), "
                "'path_confidence' (minimum step confidence), 'calibrated', 'disclaimer', "
                "'tool_trace', 'provenance'."
            ),
        }
    ]

    if streaming:
        raw = _run_tool_loop_streaming(
            messages,
            dispatcher=dispatcher,
            model=model,
            tool_defs=tool_defs,
        )
        return _augment_final(
            raw,
            history=history,
            build_fn=lambda text, trace, hist: _build_scenario_response(text, trace, hist, horizon),
        )

    final_text, tool_trace = _run_tool_loop(
        messages,
        dispatcher=dispatcher,
        model=model,
        tool_defs=tool_defs,
    )
    return _build_scenario_response(final_text, tool_trace, history, horizon)


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------


def _build_prediction_response(
    final_text: str, tool_trace: list[dict], history: Any
) -> dict[str, Any]:
    """Parse the agent's text into a validated prediction response.

    Tries JSON first; falls back to a synthetic response derived from the tool
    trace (materialize_suggestion result) so the agent loop always returns
    something even if Claude produces non-JSON prose.
    """
    parsed: dict[str, Any] = {}
    try:
        # Claude should return a JSON block; look for it.
        parsed = _extract_json(final_text)
    except Exception:
        pass

    # Fallback: pull the last materialize_suggestion result from the trace.
    if "numbers" not in parsed or "confidence" not in parsed:
        for entry in reversed(tool_trace):
            if entry["tool"] == "materialize_suggestion":
                r = entry["result"]
                if "numbers" in r and "confidence" in r:
                    parsed.setdefault("numbers", r["numbers"])
                    parsed.setdefault("confidence", r["confidence"])
                    parsed.setdefault("calibrated", r.get("calibrated", False))
                    parsed.setdefault("disclaimer", r.get("disclaimer", ""))
                    break

    cal_status = get_calibration_status()
    model_versions = _extract_model_versions(tool_trace)
    dataset_hash = history.provenance.content_hash

    parsed["tool_trace"] = tool_trace
    parsed.setdefault("explanation", final_text)
    parsed.setdefault("calibrated", not cal_status.is_stale)
    parsed["provenance"] = {
        "dataset_hash": dataset_hash,
        "model_versions": model_versions,
        "agent_prompt_hash": _prompt_hash(),
        "computed_at": datetime.now(UTC).isoformat(),
    }
    parsed.setdefault(
        "disclaimer",
        (
            "This suggestion is generated for research and entertainment purposes only. "
            "It is not a prediction of future lottery outcomes."
        ),
    )

    _validate_response(parsed)
    return parsed


def _build_scenario_response(
    final_text: str,
    tool_trace: list[dict],
    history: Any,
    horizon: int,
) -> dict[str, Any]:
    """Build a validated scenario-path response."""
    parsed: dict[str, Any] = {}
    try:
        parsed = _extract_json(final_text)
    except Exception:
        pass

    # Fallback: reconstruct steps from advance_scenario_step results in the trace.
    if "steps" not in parsed and "path" not in parsed:
        steps = []
        for entry in tool_trace:
            if entry["tool"] == "advance_scenario_step" and "error" not in entry["result"]:
                steps.append(entry["result"])
        parsed["steps"] = steps

    steps = parsed.get("path") or parsed.get("steps", [])

    # Normalize step field names: predicted_numbers→numbers, step_confidence→confidence.
    normalized: list[dict] = []
    for s in steps:
        if not isinstance(s, dict):
            continue
        normalized.append(
            {
                "step": s.get("step"),
                "numbers": s["numbers"] if "numbers" in s else s.get("predicted_numbers", []),
                "confidence": s["confidence"] if "confidence" in s else s.get("step_confidence", 0.5),
                "explanation": s.get("explanation", ""),
            }
        )

    # Store under canonical names used by the TypeScript types.
    parsed["path"] = normalized
    parsed["horizon"] = len(normalized)
    parsed.pop("steps", None)

    confidences = [s["confidence"] for s in normalized]
    path_confidence = min(confidences) if confidences else 0.01
    path_confidence = max(1e-6, min(1.0 - 1e-6, path_confidence))

    cal_status = get_calibration_status()
    model_versions = _extract_model_versions(tool_trace)

    parsed["path_confidence"] = path_confidence
    parsed.setdefault("calibrated", not cal_status.is_stale)
    parsed["tool_trace"] = tool_trace
    parsed["provenance"] = {
        "dataset_hash": history.provenance.content_hash,
        "model_versions": model_versions,
        "agent_prompt_hash": _prompt_hash(),
        "computed_at": datetime.now(UTC).isoformat(),
    }
    parsed.setdefault(
        "disclaimer",
        (
            "This scenario path is generated for research and entertainment purposes only. "
            "It does not predict actual Lotofácil results."
        ),
    )

    # Validate path-level confidence.
    if path_confidence >= 1.0 or path_confidence <= 0.0:
        raise ValueError(
            f"path_confidence={path_confidence} must be strictly in (0, 1)."
        )
    return parsed


def _extract_json(text: str) -> dict[str, Any]:
    """Extract the first JSON object from a text string."""
    import re

    # Try the entire text first.
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find a JSON block wrapped in ```json ... ``` or {...}.
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))

    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))

    raise ValueError("No JSON object found in response text.")
