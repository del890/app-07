## ADDED Requirements

### Requirement: Accept a scenario description and return 15 suggested numbers
The system SHALL accept a free-text scenario description (dream, nightmare, or lived experience) via `POST /v1/oracle/dream` and return a set of exactly 15 numbers in [1, 25], a symbolic explanation, and `artifact_type: entertainment`.

#### Scenario: Valid dream description returns 15 numbers
- **WHEN** a caller sends a non-empty scenario description to `POST /v1/oracle/dream`
- **THEN** the response contains exactly 15 distinct integers in [1, 25], a non-empty explanation, and `artifact_type: "entertainment"`

#### Scenario: Empty description is rejected
- **WHEN** a caller sends an empty or whitespace-only scenario description
- **THEN** the API returns HTTP 422 with a validation error

#### Scenario: Description too long is rejected
- **WHEN** a caller sends a scenario description exceeding 2000 characters
- **THEN** the API returns HTTP 422 with a validation error

---

### Requirement: Extract symbols via a structured tool call before number selection
The agent SHALL invoke `extract_dream_signals` and receive a list of typed symbols before any number selection occurs. Number selection without a prior `extract_dream_signals` call in the same request MUST be rejected.

#### Scenario: Agent calls extract_dream_signals first
- **WHEN** the oracle agent processes a dream description
- **THEN** the tool trace contains an `extract_dream_signals` call that precedes the `materialize_suggestion` call

#### Scenario: Missing extract step is caught
- **WHEN** the agent's tool trace does not contain `extract_dream_signals` before `materialize_suggestion`
- **THEN** the service raises an internal validation error and does not return numbers to the client

---

### Requirement: Symbol-to-number mapping is driven by a versioned symbolic catalog
The system SHALL maintain a versioned symbolic catalog in `service/src/service/oracle/catalog.py` that defines, for each `(category, label)` pair, which numbers in [1, 25] receive a probability multiplier and what the human-readable rationale is. The catalog version SHALL be included in every response.

#### Scenario: Catalog version appears in response
- **WHEN** the oracle returns a result
- **THEN** the response includes a `catalog_version` field matching the current catalog version string

#### Scenario: Unknown symbol is handled gracefully
- **WHEN** `extract_dream_signals` returns a symbol whose `(category, label)` pair is not in the catalog
- **THEN** the symbol is ignored and the remaining symbols are still applied; the explanation notes the unrecognized symbol

#### Scenario: Explicit number mentioned in dream gets a direct boost
- **WHEN** the dream description mentions a specific integer between 1 and 25 (e.g. "three cats", "the number 7")
- **THEN** the extracted symbols include a `count` category entry for that integer with elevated intensity

---

### Requirement: Bias vector is bounded and normalized before materialization
The system SHALL cap the number of applied symbols at 8 per request and normalize the resulting bias vector so that its sum equals 15 (the game's expected distribution mass) before passing it to `materialize_suggestion`.

#### Scenario: More than 8 symbols are truncated by intensity
- **WHEN** `extract_dream_signals` returns more than 8 symbols
- **THEN** only the top 8 by intensity are applied to the bias vector

#### Scenario: Bias vector sums to 15 after normalization
- **WHEN** the bias vector is computed from the catalog
- **THEN** the vector is normalized so that sum(bias_vector) == 15.0 before `materialize_suggestion` is called

---

### Requirement: Response is labelled entertainment, not prediction or research
Every response from `POST /v1/oracle/dream` SHALL carry `artifact_type: "entertainment"` and a fixed disclaimer that the numbers are derived from symbolic mapping and have no statistical or predictive basis.

#### Scenario: Correct artifact type
- **WHEN** the oracle returns any result
- **THEN** `artifact_type` is exactly `"entertainment"`

#### Scenario: Disclaimer is present
- **WHEN** the oracle returns any result
- **THEN** the `disclaimer` field is non-empty and contains no language implying prediction, guarantee, or causality

---

### Requirement: Streaming SSE response is supported
The endpoint SHALL support streaming via `text/event-stream` using the same SSE event schema as `/v1/predictions/next-draw` (`tool_start`, `tool_result`, `final`).

#### Scenario: SSE stream contains tool events
- **WHEN** a caller sends `Accept: text/event-stream`
- **THEN** the response is a stream of SSE events including at least one `tool_start` and one `tool_result` event before the `final` event

#### Scenario: JSON fallback works without Accept header
- **WHEN** a caller omits the `Accept` header or sends `application/json`
- **THEN** the response is a single JSON object with the full oracle result

---

### Requirement: Dream input is not persisted
The system SHALL NOT log, store, or persist the raw dream/scenario description text at any point during or after processing.

#### Scenario: No storage of dream text
- **WHEN** the oracle processes a dream description
- **THEN** no file, database, or log entry contains the raw description text after the request completes

---

### Requirement: Client page streams and displays the interpretation
The client SHALL provide a page at `/play/dream` that sends the dream description to the oracle endpoint, streams the agent's reasoning via SSE, and displays the 15 numbers alongside the symbolic explanation once complete.

#### Scenario: User submits a dream and sees 15 numbers
- **WHEN** a user types a dream description and submits the form
- **THEN** the page shows the agent's tool events streaming in real time and, on completion, renders the 15 suggested numbers and the symbolic explanation

#### Scenario: Entertainment disclaimer is always visible
- **WHEN** the dream oracle page is loaded
- **THEN** a disclaimer stating that results are for entertainment only is visible before and after submission
