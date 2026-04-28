## ADDED Requirements

### Requirement: Scan endpoint accepts ticket image
The service SHALL expose `POST /v1/tickets/scan` accepting `multipart/form-data` with a single field `image` (JPEG or PNG). The endpoint SHALL reject requests where the image exceeds 4 MB with HTTP 413.

#### Scenario: Valid image accepted
- **WHEN** a client POSTs a valid JPEG/PNG under 4 MB to `/v1/tickets/scan`
- **THEN** the service SHALL respond with HTTP 200 and a JSON body matching the `ScannedTicket` schema

#### Scenario: Image too large
- **WHEN** a client POSTs an image larger than 4 MB
- **THEN** the service SHALL respond with HTTP 413 and a descriptive error message

#### Scenario: Non-image content type rejected
- **WHEN** a client POSTs a file that is not JPEG or PNG
- **THEN** the service SHALL respond with HTTP 422

### Requirement: Claude Vision detects marked numbers
The service SHALL send the uploaded image to the Anthropic API using a vision-capable model with a structured prompt instructing it to identify marked cells in each game grid. The model response SHALL be parsed into an array of integer arrays.

#### Scenario: Numbers detected successfully
- **WHEN** the model returns valid JSON with a `games` array
- **THEN** each inner array SHALL contain only integers between 1 and 25
- **THEN** the response SHALL include only grids where at least one number is marked

#### Scenario: Model returns malformed JSON
- **WHEN** the model response cannot be parsed as the expected schema
- **THEN** the service SHALL respond with HTTP 422 and an `unreadable_ticket` error code

#### Scenario: No marked numbers detected
- **WHEN** the model finds no marked cells in any grid
- **THEN** the service SHALL respond with HTTP 422 and a `no_marks_detected` error code

### Requirement: Scan endpoint rate-limited
The `/v1/tickets/scan` endpoint SHALL be subject to the same per-IP rate limit configured by `PREDICTIONS_RATE_LIMIT_PER_MINUTE`.

#### Scenario: Rate limit exceeded
- **WHEN** a client exceeds `PREDICTIONS_RATE_LIMIT_PER_MINUTE` requests per minute
- **THEN** the service SHALL respond with HTTP 429

### Requirement: ScannedTicket response schema
The `ScannedTicket` response SHALL be a JSON object `{"games": [[int, ...], ...]}` where each inner array is a sorted list of unique integers 1–25 representing marked numbers in one game grid.

#### Scenario: Single game grid returned
- **WHEN** the ticket image contains one filled game grid with 15 marked numbers
- **THEN** the response SHALL be `{"games": [[<15 sorted integers>]]}`

#### Scenario: Multiple game grids returned
- **WHEN** the ticket image contains three filled game grids
- **THEN** the response SHALL contain three inner arrays in grid order (top to bottom)
