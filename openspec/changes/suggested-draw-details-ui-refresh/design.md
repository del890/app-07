## Context

The prediction card currently displays explanation content as a raw JSON blob when the model returns structured metadata as a serialized object string. This produces poor readability on both desktop and mobile and hides the most important insights behind dense machine-oriented text.

The client already has reusable play-surface components and receives stable prediction payloads, so this change can be implemented as a presentation-layer enhancement with lightweight parsing and formatting logic.

## Goals / Non-Goals

**Goals:**
- Normalize explanation payloads that may arrive as plain text, JSON string, or object-like content.
- Render a structured explanation layout with clear sections (summary, evidence highlights, top probabilities, provenance).
- Keep behavior resilient by degrading to readable plain text when parsing fails.
- Reuse the same explanation presentation in both next-draw and scenario result cards.

**Non-Goals:**
- Changing service-side inference logic, ranking logic, or API contracts.
- Introducing external UI or parsing libraries.
- Reworking unrelated play page interactions.

## Decisions

### D1 - Introduce an explanation normalizer utility in the client
Decision: Add a small formatter/parser utility that takes raw explanation input and returns a typed normalized view model used by the card UI.

Rationale: Keeps parsing concerns out of Vue templates and allows consistent rendering across pages.

Alternatives considered:
- Parse inline inside component templates: rejected due to duplicated logic and lower testability.
- Move normalization to backend: rejected because request scope is presentation-only and no API change is required.

### D2 - Render explanation as sectioned content instead of monolithic text
Decision: Use a sectioned layout with optional blocks: summary paragraph, highlight bullet groups, probability chips/table, and provenance metadata footer.

Rationale: Users can quickly scan key evidence and confidence drivers without reading a full JSON document.

Alternatives considered:
- Pretty-print JSON in a code block: rejected as still technical and visually heavy.
- Flatten all fields into one paragraph: rejected due to poor scannability.

### D3 - Define strict fallback behavior for malformed or sparse payloads
Decision: If parsing fails or expected fields are absent, show a concise fallback card section with a plain-language message and sanitized raw explanation text.

Rationale: Guarantees deterministic UI and avoids blank cards or runtime rendering errors.

Alternatives considered:
- Hide explanation when parse fails: rejected because users lose context entirely.
- Throw UI error state: rejected as too disruptive for non-critical metadata.

### D4 - Reuse existing card surfaces with an explanation subcomponent
Decision: Keep existing prediction card shell and replace only the explanation region with a reusable renderer subcomponent/composable.

Rationale: Minimizes regression risk and keeps visual consistency with existing numbers and confidence surfaces.

Alternatives considered:
- Replace entire card component: rejected because it increases change surface unnecessarily.

## Risks / Trade-offs

- Parsing heuristics may misclassify edge-case free-form text as JSON-like content -> Mitigation: parse only when input starts with `{` or `[` and fallback immediately on exception.
- Structured UI may look sparse for minimal payloads -> Mitigation: conditionally hide empty sections and keep summary/fallback always present.
- Slight increase in client-side formatting logic -> Mitigation: encapsulate logic in one utility with unit tests for representative payload variants.
