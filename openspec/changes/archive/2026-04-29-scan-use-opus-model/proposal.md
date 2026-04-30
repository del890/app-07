## Why

The ticket scan endpoint currently uses `DEFAULT_MODEL` (`claude-sonnet-4-6`) for vision analysis. Ticket images are often taken under poor lighting or at a slight angle, and accurate spatial reasoning over the 5×5 grid is critical — a single wrong number ruins the result. `claude-opus-4-7` (HEAVY_MODEL) has significantly stronger vision and spatial reasoning, making it the right choice for this high-accuracy, low-frequency operation.

## What Changes

- The `POST /v1/tickets/scan` endpoint switches from `DEFAULT_MODEL` to `HEAVY_MODEL` (`claude-opus-4-7`) for its Claude Vision call.
- All other service operations (prediction agent, etc.) continue using `DEFAULT_MODEL` or `CHEAP_MODEL` — unchanged.

## Capabilities

### New Capabilities

<!-- None — no new product capability is introduced. -->

### Modified Capabilities

<!-- No spec-level behavioral requirements change. The scan API contract (request/response schema) is identical. This is an implementation detail (model selection) that doesn't affect observable behavior from a requirements perspective. -->

## Impact

- **`service/src/service/api/tickets.py`**: Replace `DEFAULT_MODEL` import/usage with `HEAVY_MODEL` for the scan call and its log entry.
- No changes to `useTicketScanner.ts`, the API schema, or any other service component.
