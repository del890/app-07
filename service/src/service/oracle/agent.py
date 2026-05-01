"""LLM-powered dream-oracle agent.

Orchestrates a tool-use loop to interpret a free-text dream description and
produce 15 Lotofácil number suggestions via symbolic mapping.

Design invariants:
- The agent MUST call ``extract_dream_signals`` before ``materialize_suggestion``.
  This ordering is enforced by ``_validate_tool_trace_order``.
- Numbers in the final response MUST come from ``materialize_suggestion``.
- The raw dream description is never stored or logged.
- All responses carry ``artifact_type: "entertainment"``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from typing import Any, Iterator

from service.llm.client import DEFAULT_MODEL, get_anthropic, with_cache_control
from service.oracle.guard import check_dream_description
from service.oracle.models import DreamOracleResult, ExtractedSymbol
from service.oracle.prompt import ORACLE_DISCLAIMER, ORACLE_SYSTEM_PROMPT
from service.oracle.tools import OracleToolDispatcher, build_oracle_tool_definitions

logger = logging.getLogger(__name__)

MAX_ORACLE_TOOL_CALLS = 10


def _prompt_hash() -> str:
    return hashlib.sha256(ORACLE_SYSTEM_PROMPT.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Tool trace validation
# ---------------------------------------------------------------------------


def _validate_tool_trace_order(tool_trace: list[dict]) -> None:
    """Raise ValueError if extract_dream_signals did not precede materialize_suggestion."""
    tool_names = [e["tool"] for e in tool_trace]
    has_extract = "extract_dream_signals" in tool_names
    has_materialize = "materialize_suggestion" in tool_names

    if has_materialize and not has_extract:
        raise ValueError(
            "Oracle agent violated the tool order constraint: "
            "materialize_suggestion was called without a prior extract_dream_signals call."
        )

    if has_extract and has_materialize:
        extract_idx = tool_names.index("extract_dream_signals")
        materialize_idx = tool_names.index("materialize_suggestion")
        if materialize_idx < extract_idx:
            raise ValueError(
                "Oracle agent violated the tool order constraint: "
                "materialize_suggestion appeared before extract_dream_signals in the trace."
            )


# ---------------------------------------------------------------------------
# JSON extraction helper
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> dict[str, Any]:
    """Extract the first JSON object from a text block."""
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in agent text.")
    return json.loads(text[start:end])


# ---------------------------------------------------------------------------
# Tool-use loop (non-streaming)
# ---------------------------------------------------------------------------


def _run_oracle_tool_loop(
    messages: list[dict],
    *,
    dispatcher: OracleToolDispatcher,
    model: str,
    tool_defs: list[dict],
    max_tool_calls: int = MAX_ORACLE_TOOL_CALLS,
) -> tuple[str, list[dict]]:
    """Run the oracle tool-use loop synchronously.

    Returns
    -------
    final_text : str
    tool_trace : list[dict]
    """
    from service.token_counters import record as record_tokens

    client = get_anthropic()
    tool_trace: list[dict] = []
    call_count = 0

    while call_count < max_tool_calls:
        resp = client.messages.create(
            model=model,
            max_tokens=2048,
            system=with_cache_control(ORACLE_SYSTEM_PROMPT),
            tools=with_cache_control(tool_defs),
            messages=messages,
        )

        if hasattr(resp, "usage") and resp.usage is not None:
            record_tokens(
                input_tokens=getattr(resp.usage, "input_tokens", 0),
                output_tokens=getattr(resp.usage, "output_tokens", 0),
            )

        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "end_turn":
            final_text = ""
            for block in resp.content:
                if hasattr(block, "text"):
                    final_text = block.text
            return final_text, tool_trace

        if resp.stop_reason != "tool_use":
            final_text = ""
            for block in resp.content:
                if hasattr(block, "text"):
                    final_text = block.text
            return final_text, tool_trace

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

    return "", tool_trace


# ---------------------------------------------------------------------------
# Tool-use loop (streaming)
# ---------------------------------------------------------------------------


def _run_oracle_tool_loop_streaming(
    messages: list[dict],
    *,
    dispatcher: OracleToolDispatcher,
    model: str,
    tool_defs: list[dict],
    max_tool_calls: int = MAX_ORACLE_TOOL_CALLS,
) -> Iterator[dict]:
    """Yield SSE-friendly event dicts during the oracle tool-use loop."""
    from service.token_counters import record as record_tokens

    client = get_anthropic()
    tool_trace: list[dict] = []
    call_count = 0

    while call_count < max_tool_calls:
        resp = client.messages.create(
            model=model,
            max_tokens=2048,
            system=with_cache_control(ORACLE_SYSTEM_PROMPT),
            tools=with_cache_control(tool_defs),
            messages=messages,
        )

        if hasattr(resp, "usage") and resp.usage is not None:
            record_tokens(
                input_tokens=getattr(resp.usage, "input_tokens", 0),
                output_tokens=getattr(resp.usage, "output_tokens", 0),
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
            yield {"type": "tool_start", "tool_name": block.name, "tool_input": dict(block.input)}
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
                "tool_name": block.name,
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
# Response builder
# ---------------------------------------------------------------------------


def _build_oracle_response(final_text: str, tool_trace: list[dict]) -> dict[str, Any]:
    """Parse the agent's text into a validated DreamOracleResult dict."""
    _validate_tool_trace_order(tool_trace)

    parsed: dict[str, Any] = {}
    try:
        parsed = _extract_json(final_text)
    except Exception:
        pass

    # Fallback: reconstruct from tool trace if agent didn't produce JSON.
    if "numbers" not in parsed:
        for entry in reversed(tool_trace):
            if entry["tool"] == "materialize_suggestion" and "numbers" in entry.get("result", {}):
                parsed.setdefault("numbers", entry["result"]["numbers"])
                break

    if "symbols" not in parsed:
        for entry in tool_trace:
            if entry["tool"] == "extract_dream_signals":
                inp = entry.get("input", {})
                parsed.setdefault("symbols", inp.get("symbols", []))
                break

    if "catalog_version" not in parsed:
        for entry in tool_trace:
            if entry["tool"] == "extract_dream_signals":
                parsed.setdefault(
                    "catalog_version",
                    entry.get("result", {}).get("catalog_version", "unknown"),
                )
                break

    parsed["artifact_type"] = "entertainment"
    parsed.setdefault("disclaimer", ORACLE_DISCLAIMER)

    # Explanation fallback: if still missing, attempt a second JSON parse of
    # final_text (handles the case where _extract_json succeeded but the outer
    # JSON had no "explanation" key, or failed entirely).
    if "explanation" not in parsed:
        raw_explanation = final_text or ""
        # Strip markdown code fences before trying to extract explanation.
        stripped = re.sub(r"^```[a-z]*\s*", "", raw_explanation.strip(), flags=re.I)
        stripped = re.sub(r"\s*```$", "", stripped.strip())
        try:
            inner = json.loads(stripped)
            raw_explanation = inner.get("explanation", raw_explanation)
        except Exception:
            pass
        # If the "explanation" still looks like raw JSON, replace with a neutral message.
        cleaned = raw_explanation.strip()
        if cleaned.startswith("{") or cleaned.startswith("```"):
            cleaned = "Interpretação indisponível."
        parsed["explanation"] = cleaned or "Interpretação indisponível."

    # Validate required fields.
    if "numbers" not in parsed or len(parsed.get("numbers", [])) != 15:
        raise ValueError(
            f"Oracle agent did not produce 15 numbers. Got: {parsed.get('numbers')}"
        )

    return parsed


# ---------------------------------------------------------------------------
# Streaming augmenter
# ---------------------------------------------------------------------------


def _augment_oracle_final(gen: Iterator[dict]) -> Iterator[dict]:
    """Pass through all events; enrich the ``final`` event with the built result."""
    for event in gen:
        if event.get("type") == "final":
            try:
                built = _build_oracle_response(
                    event.get("text", ""),
                    event.get("tool_trace", []),
                )
            except Exception as exc:
                built = {"error": str(exc)}
            yield {**event, "result": built}
        else:
            yield event


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def interpret_dream(
    description: str,
    *,
    model: str = DEFAULT_MODEL,
    streaming: bool = False,
) -> dict[str, Any] | Iterator[dict[str, Any]]:
    """Interpret a dream description and return 15 Lotofácil number suggestions.

    Parameters
    ----------
    description : str
        The dream or scenario text. Never stored or logged.
    model : str
        Anthropic model to use.
    streaming : bool
        If True, return an iterator of SSE-style event dicts.

    Returns
    -------
    dict[str, Any]
        When ``streaming=False``: a validated oracle result dict.
    Iterator[dict[str, Any]]
        When ``streaming=True``: event stream ending with a ``final`` event.
    """
    # NOTE: `description` is intentionally NOT logged anywhere in this function.
    # Guard: reject prompt-injection attempts before touching the LLM.
    check_dream_description(description)

    tool_defs = build_oracle_tool_definitions()
    dispatcher = OracleToolDispatcher()
    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                "Please interpret this dream and suggest 15 Lotofácil numbers "
                "using the symbolic oracle tools.\n\n"
                f"Dream description:\n{description}"
            ),
        }
    ]

    if streaming:
        raw = _run_oracle_tool_loop_streaming(
            messages,
            dispatcher=dispatcher,
            model=model,
            tool_defs=tool_defs,
        )
        return _augment_oracle_final(raw)

    final_text, tool_trace = _run_oracle_tool_loop(
        messages,
        dispatcher=dispatcher,
        model=model,
        tool_defs=tool_defs,
    )
    return _build_oracle_response(final_text, tool_trace)
