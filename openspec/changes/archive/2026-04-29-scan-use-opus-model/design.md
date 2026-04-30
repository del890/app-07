## Context

The service defines three model tiers in `service/src/service/llm/client.py`:

| Constant | Model | Use case |
|---|---|---|
| `DEFAULT_MODEL` | `claude-sonnet-4-6` | General agent tasks |
| `HEAVY_MODEL` | `claude-opus-4-7` | High-accuracy, complex reasoning |
| `CHEAP_MODEL` | `claude-haiku-4-5-20251001` | Fast, low-cost tasks |

The ticket scan endpoint (`POST /v1/tickets/scan`) currently imports and uses `DEFAULT_MODEL`. The change is to import `HEAVY_MODEL` and use it for that single call.

## Goals / Non-Goals

**Goals:**
- Use `HEAVY_MODEL` for the Claude Vision call in `tickets.py`.
- Ensure the log entry also records the correct model name.

**Non-Goals:**
- Changing `DEFAULT_MODEL` globally — all other endpoints stay on Sonnet.
- Adding a config flag to select the scan model at runtime — not needed; Opus is the deliberate choice.
- Any change to the API contract, client code, or prompts.

## Decisions

### 1. Hard-code `HEAVY_MODEL` in `tickets.py` rather than a new config variable

**Choice**: Import `HEAVY_MODEL` from `service.llm.client` and use it directly, the same way `DEFAULT_MODEL` is used everywhere else.

**Alternatives considered**:
- *New env var `SCAN_MODEL`*: Adds operational complexity for a choice that should be intentional, not accidental. If the model needs to change in future, a code change + review is the right gate.
- *Pass model as a query param from the client*: Security anti-pattern — callers should not control which model the service uses.

**Rationale**: The model tier constants already exist for exactly this purpose. Using them is consistent with the established pattern and requires zero new infrastructure.

## Risks / Trade-offs

- **Higher cost per scan**: Opus is more expensive than Sonnet. Ticket scans are infrequent (one per user session) so the absolute cost increase is negligible.
- **Slightly slower response**: Opus may take a few seconds longer. Acceptable — the scan call already involves image upload and is inherently async from the user's perspective.

## Migration Plan

Single-file change. No migration needed; the API surface is identical. Rollback is reverting the two-line diff.
