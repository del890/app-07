---
name: service-stack
description: Enforces the service tech stack for this project. Use whenever building, scaffolding, or modifying server-side / backend code, APIs, workers, or anything described as "the service" / "the backend". The service MUST be built in Python and designed around LLM-powered agents.
---

# Service Stack

The service (backend) for this project **must** be built with:

- **Language**: Python (3.11+)
- **Paradigm**: Agent-based — the core of the service is one or more LLM-powered agents, not a classical CRUD backend
- **LLM**: Use a first-class LLM provider SDK (default: Anthropic `anthropic` SDK with Claude models; only swap if the user explicitly asks)

Apply this skill any time you are creating, scaffolding, or modifying service-side code. Do not substitute another language (no Node, Go, Ruby, Rust, Java, etc.) for the service unless the user explicitly overrides this rule.

---

## Required setup

When scaffolding a new service, use a modern Python toolchain:

```bash
mkdir service && cd service
uv init            # or: python -m venv .venv && source .venv/bin/activate
uv add anthropic pydantic fastapi uvicorn python-dotenv
uv add --dev ruff mypy pytest
```

Baseline conventions:

1. **Dependency + env management**: use [`uv`](https://docs.astral.sh/uv/) (preferred) or `pip` + `venv`. Always pin via `pyproject.toml` — no unpinned `requirements.txt`.
2. **Types**: type-annotate every public function. Run `mypy --strict` (or at minimum `mypy` with `disallow_untyped_defs`).
3. **Validation**: use **Pydantic v2** models for all inbound/outbound data and for tool schemas.
4. **Style**: format and lint with **Ruff**. No Black, no isort — Ruff replaces them.
5. **Tests**: `pytest` under `tests/`. Mock external LLM calls in unit tests; keep a small set of live integration tests behind a flag.
6. **Config**: load secrets from env vars (`python-dotenv` in dev). Never hardcode API keys.

---

## Agent architecture

The service is **agent-first**. An agent here means an LLM-driven loop that can reason, call tools, and produce outputs — not a thin wrapper that makes a single completion call.

**Minimum shape of an agent:**

```python
# service/agents/base.py
from anthropic import Anthropic
from pydantic import BaseModel

class AgentResult(BaseModel):
    output: str
    tool_calls: list[dict]
    usage: dict

class Agent:
    def __init__(self, *, system: str, tools: list[dict], model: str = "claude-sonnet-4-6"):
        self.client = Anthropic()
        self.system = system
        self.tools = tools
        self.model = model

    def run(self, user_input: str) -> AgentResult:
        # Tool-use loop: call model, dispatch tool calls, feed results back
        # until stop_reason == "end_turn".
        ...
```

**Conventions for agents:**

- **Tool definitions**: declare tools with JSON Schema (Pydantic → `.model_json_schema()` is fine). Each tool has a typed Python handler.
- **Tool-use loop**: handle `stop_reason == "tool_use"` by executing handlers and re-prompting with `tool_result` blocks until `end_turn`.
- **Prompt caching**: enable `cache_control` on stable system prompts and tool definitions to cut cost/latency. (See the `claude-api` skill when wiring this up.)
- **Structured outputs**: for any agent that needs machine-readable output, use tool use (forced tool choice) or Pydantic-validated JSON — never parse free-form prose.
- **Model defaults**: use the latest Claude family. Default to `claude-sonnet-4-6` for general work; escalate to `claude-opus-4-7` for harder reasoning; use `claude-haiku-4-5-20251001` for cheap/fast subtasks.
- **Observability**: log `request_id`, `model`, `input_tokens`, `output_tokens`, `cache_read_input_tokens`, and `stop_reason` for every LLM call.
- **Safety**: validate tool arguments with Pydantic before execution. Treat model output as untrusted input.

---

## API surface

If the service exposes HTTP:

- Framework: **FastAPI** (`uvicorn` for dev, `uvicorn`/`gunicorn` + workers for prod).
- Request/response models are Pydantic.
- Streaming agent responses: use FastAPI's `StreamingResponse` with SSE, forwarding Anthropic's streaming events.
- Background / long-running agent jobs: run them out-of-band (e.g. a task queue or a simple worker process) rather than blocking the HTTP request.

---

## Directory layout

```
service/
  pyproject.toml
  src/service/
    __init__.py
    main.py              # FastAPI app entrypoint
    agents/              # agent definitions, one file per agent
    tools/               # tool handlers (typed, Pydantic-validated)
    prompts/             # system prompts as .md or .py constants
    models/              # shared Pydantic models
    llm/                 # Anthropic client factory, retry/caching helpers
    config.py            # settings via pydantic-settings
  tests/
```

---

## Guardrails

- If the user asks to build service/backend/API code and no service exists yet, scaffold it as Python + agents + LLM per above.
- If an existing service is present, verify it is Python before extending it. If it is not, stop and flag the mismatch rather than silently adding to a non-conforming stack.
- Do not introduce a non-Python runtime (Node, Go, etc.) into the service.
- Do not build a "dumb" CRUD backend where the core job should be agent work — push logic into an agent with tools instead of hardcoding it.
- Do not call the LLM with raw `requests`/`httpx` when the official SDK covers the need — use `anthropic`.
- When writing LLM code, also consult the `claude-api` skill for caching, tool use, and model selection details.
- If the user explicitly overrides this rule for a specific task, follow their instruction but call out that you are deviating from the project's service stack.
