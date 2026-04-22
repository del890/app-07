## ADDED Requirements

### Requirement: Expose HTTP API covering all capabilities
The service SHALL expose an HTTP API that gives clients access to ingestion metadata, statistical analysis, external-signal correlation, and prediction-engine outputs. The API MUST use JSON request/response bodies validated by Pydantic models.

#### Scenario: Canonical endpoint set exists
- **WHEN** a client queries the API index
- **THEN** the response advertises at minimum: `GET /dataset`, `GET /statistics/*`, `POST /correlations`, `POST /predictions/next-draw`, `POST /predictions/scenario-path`, and `GET /health`

#### Scenario: Unknown endpoint returns structured 404
- **WHEN** a client requests an undefined endpoint
- **THEN** the service returns HTTP 404 with a JSON body `{ "error": { "code": "not_found", "message": ... } }`

### Requirement: Stream long-running agent responses
Prediction endpoints MUST support streaming (Server-Sent Events) so that clients can render tool calls and partial agent output as they occur, in addition to a non-streaming mode that returns the complete result.

#### Scenario: Streaming prediction
- **WHEN** a client requests `POST /predictions/next-draw` with `Accept: text/event-stream`
- **THEN** the service streams agent events (tool starts, tool results, final output) as SSE events and closes the stream when complete

#### Scenario: Non-streaming prediction
- **WHEN** a client requests the same endpoint with `Accept: application/json`
- **THEN** the service returns the complete prediction as a single JSON response

### Requirement: Consistent error envelope
All error responses MUST use a single documented error envelope: `{ "error": { "code": "<machine_code>", "message": "<human>", "details": { ... } } }`. HTTP status codes MUST match the error class (400 for validation, 404 for missing, 409 for state conflict, 429 for rate limit, 5xx for server).

#### Scenario: Validation error
- **WHEN** a client submits a malformed request body
- **THEN** the service returns HTTP 400 with the canonical error envelope and `details` enumerating each invalid field

#### Scenario: Upstream LLM failure
- **WHEN** the Anthropic API call inside a prediction fails
- **THEN** the service returns HTTP 502 with error code `llm_upstream_error` and does not leak the upstream stack trace

### Requirement: Honest rate limiting and backpressure
The service MUST apply per-client rate limits on prediction endpoints to protect the LLM quota, and MUST return HTTP 429 with `Retry-After` when a client exceeds its budget.

#### Scenario: Rate limit exceeded
- **WHEN** a client exceeds the configured per-minute budget on `/predictions/*`
- **THEN** the service returns HTTP 429 with the canonical error envelope and a `Retry-After` header

### Requirement: Health and readiness probes
The service MUST expose `GET /health` (liveness) and `GET /ready` (readiness). Readiness MUST return 503 until ingestion has successfully loaded `data.json` and — for the play surface — until prediction-engine calibration has completed successfully.

#### Scenario: Liveness always responds
- **WHEN** the service process is up
- **THEN** `GET /health` returns 200 with `{ "status": "ok" }`

#### Scenario: Readiness reflects ingestion and calibration state
- **WHEN** ingestion has not completed
- **THEN** `GET /ready` returns 503 with a body describing which precondition is missing

### Requirement: Structured, traceable logs
Every request MUST produce a structured log entry with: request id, route, status, duration, client id (if any), dataset hash, and — for prediction requests — model versions and tool-call count. LLM calls internal to a request MUST log token usage.

#### Scenario: Request log is emitted
- **WHEN** any request completes
- **THEN** a single structured log line is emitted containing the fields listed above

### Requirement: Authentication and secret handling
The service MUST read the Anthropic API key from an environment variable and MUST NOT echo it in any response, log, or error message. If the key is missing at startup, the service MUST refuse to start with a clear error.

#### Scenario: Missing key fails startup
- **WHEN** the service starts without `ANTHROPIC_API_KEY`
- **THEN** startup aborts with a clear error naming the missing variable

#### Scenario: Secret never leaks
- **WHEN** any error path runs
- **THEN** no log line, response body, or stack trace contains the value of `ANTHROPIC_API_KEY`

### Requirement: Versioned API surface
The API MUST be served under a version prefix (`/v1/...`) so that future breaking changes can be introduced under `/v2` without disrupting existing clients.

#### Scenario: All endpoints are versioned
- **WHEN** any endpoint is exposed
- **THEN** its path begins with `/v1/`
