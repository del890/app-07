## ADDED Requirements

### Requirement: Explanation payloads SHALL be normalized before rendering
The client SHALL normalize prediction explanation content into a structured view model before rendering. Normalization MUST support plain text, serialized JSON strings, and object-like payload content.

#### Scenario: JSON string explanation is parsed
- **WHEN** the explanation payload is a valid JSON string containing fields such as `summary` and `top_probabilities`
- **THEN** the client parses the payload and exposes these fields through the normalized explanation model

#### Scenario: Plain text explanation bypasses structured parsing
- **WHEN** the explanation payload is natural-language text and not valid JSON
- **THEN** the client preserves the text as fallback summary content without throwing rendering errors

### Requirement: Suggested-draw explanation SHALL render as sectioned, readable UI
The prediction result UI SHALL render explanation content in structured sections instead of showing raw JSON text. The UI MUST support, when available: summary, key highlight groups, top probability items, and provenance details.

#### Scenario: Structured explanation shows summary and highlights
- **WHEN** normalized explanation includes summary and highlight groups
- **THEN** the card shows a summary block followed by labeled highlight sections with human-readable bullets

#### Scenario: Probability entries render as compact metrics
- **WHEN** normalized explanation includes top probability items
- **THEN** the card shows each item as a compact metric element with number and probability value

### Requirement: Explanation rendering MUST degrade gracefully on malformed data
If explanation normalization fails or returns partial data, the UI MUST still render a valid explanation area using safe fallback content.

#### Scenario: Malformed JSON does not break card rendering
- **WHEN** the explanation payload starts like JSON but parsing fails
- **THEN** the card renders fallback explanatory text and does not render raw parser errors

#### Scenario: Missing optional sections are omitted cleanly
- **WHEN** normalized explanation lacks probabilities or provenance
- **THEN** those sections are omitted without empty placeholders and the remaining sections remain readable

### Requirement: Explanation presentation SHALL be consistent across play result surfaces
Both next-draw and scenario step result cards SHALL use the same explanation normalization and rendering behavior.

#### Scenario: Next-draw and scenario cards match structure
- **WHEN** equivalent normalized explanation data is provided to next-draw and scenario cards
- **THEN** both surfaces render the same section ordering and formatting conventions
