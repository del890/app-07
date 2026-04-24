"""Global token-usage counters for the prediction service.

Counters are incremented by the agent module after every LLM call.
They are exposed on `/v1/ready` so operators can track spend without
needing a sidecar metrics collector.

All counters are in-process and reset on restart — they are for
observability/ops, not billing.
"""

from __future__ import annotations

from threading import Lock

_lock = Lock()

_input_tokens: int = 0
_output_tokens: int = 0
_llm_calls: int = 0


def record(*, input_tokens: int, output_tokens: int) -> None:
    """Increment counters after one LLM API call."""
    global _input_tokens, _output_tokens, _llm_calls
    with _lock:
        _input_tokens += input_tokens
        _output_tokens += output_tokens
        _llm_calls += 1


def snapshot() -> dict[str, int]:
    """Return a point-in-time snapshot (safe to call from any thread)."""
    with _lock:
        return {
            "llm_calls": _llm_calls,
            "input_tokens": _input_tokens,
            "output_tokens": _output_tokens,
            "total_tokens": _input_tokens + _output_tokens,
        }


def reset() -> None:
    """Reset counters — for tests only."""
    global _input_tokens, _output_tokens, _llm_calls
    with _lock:
        _input_tokens = 0
        _output_tokens = 0
        _llm_calls = 0
