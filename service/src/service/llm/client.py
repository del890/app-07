"""Anthropic client factory with prompt-caching helpers and retry defaults.

Usage::

    from service.llm.client import get_anthropic, with_cache_control
    client = get_anthropic()
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=with_cache_control(SYSTEM_PROMPT),
        tools=with_cache_control(TOOL_DEFS),
        messages=[...],
    )

The retry/backoff policy is handed to the Anthropic SDK, which already supports
automatic retries on transient errors; we just choose the knobs.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from anthropic import Anthropic

from service.config import ConfigError, get_settings

# Default model tiers (see design.md §5). Keep in sync with the service-stack skill.
DEFAULT_MODEL = "claude-sonnet-4-6"
HEAVY_MODEL = "claude-opus-4-7"
CHEAP_MODEL = "claude-haiku-4-5-20251001"


@lru_cache(maxsize=1)
def get_anthropic() -> Anthropic:
    """Return a process-wide Anthropic client.

    Raises ConfigError if ANTHROPIC_API_KEY is missing — callers should normally
    rely on ``require_runtime_ready`` at startup instead of hitting this lazily.
    """
    settings = get_settings()
    if settings.anthropic_api_key is None:
        raise ConfigError("ANTHROPIC_API_KEY is not set; cannot build Anthropic client.")
    return Anthropic(
        api_key=settings.anthropic_api_key.get_secret_value(),
        max_retries=3,
        timeout=60.0,
    )


def with_cache_control(value: Any) -> Any:
    """Mark the last block of a system/tool payload with ephemeral cache control.

    Accepts either a plain string (wraps it into a single text block) or a list
    of blocks (tags the last entry). The Anthropic API caches the prefix of the
    prompt up to and including a block marked with ``cache_control``.

    Cache-control is applied in two standard places per the claude-api skill:
    the system prompt and the tool definitions block.
    """
    if isinstance(value, str):
        return [
            {
                "type": "text",
                "text": value,
                "cache_control": {"type": "ephemeral"},
            }
        ]
    if isinstance(value, list) and value:
        # Don't mutate caller state — shallow copy + replace the last entry.
        marked = list(value)
        last = dict(marked[-1])
        last["cache_control"] = {"type": "ephemeral"}
        marked[-1] = last
        return marked
    return value
