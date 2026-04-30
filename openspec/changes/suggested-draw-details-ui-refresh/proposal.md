## Why

The suggested-draw explanation is currently rendered as a raw JSON object, which is hard to scan and undermines trust in the generated insights. Improving this presentation now will make the recommendation easier to understand and more visually credible without changing prediction logic.

## What Changes

- Parse explanation payloads that arrive as JSON strings or objects and map them into structured UI sections.
- Replace the raw JSON text block with a designed summary view containing clear headings, short highlight bullets, and compact metric chips.
- Add graceful fallback rendering when explanation parsing fails or fields are missing, so users always see useful content.
- Apply the same explanation renderer to both single suggested draw and scenario-step cards to keep consistency.

## Capabilities

### New Capabilities
- `suggested-draw-explanation-presentation`: Structured, user-friendly rendering for suggested-draw explanation content (summary, evidence highlights, probabilities, provenance), including robust fallback behavior.

### Modified Capabilities
- *(none)*

## Impact

- Affected client components in the prediction result surface (primarily card-level rendering for explanation content).
- No backend API contract changes required; this is a client presentation and parsing upgrade.
- May add a small formatter/parser utility in the client for explanation normalization.
