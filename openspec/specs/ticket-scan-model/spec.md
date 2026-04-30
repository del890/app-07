### Requirement: Ticket scan uses the high-accuracy vision model
The ticket scan endpoint (`POST /v1/tickets/scan`) SHALL use the service's `HEAVY_MODEL` (`claude-opus-4-7`) for its Claude Vision call, not the `DEFAULT_MODEL`.

#### Scenario: Scan request uses Opus model
- **WHEN** a client submits a valid ticket image to `POST /v1/tickets/scan`
- **THEN** the service SHALL invoke Claude with `claude-opus-4-7`
- **AND** the scan log entry SHALL record `claude-opus-4-7` as the model used

#### Scenario: Other endpoints are unaffected
- **WHEN** any endpoint other than `/v1/tickets/scan` calls the LLM
- **THEN** it SHALL continue using `DEFAULT_MODEL` or `CHEAP_MODEL` as previously configured
