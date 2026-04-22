## ADDED Requirements

### Requirement: Ingest historical dataset from data.json
The system SHALL ingest the historical Lotofácil dataset from `data.json` at the repository root as its primary, read-only data source. The dataset MUST be treated as immutable input; the ingestion layer SHALL never mutate `data.json`.

#### Scenario: Dataset loads successfully at startup
- **WHEN** the service starts with a valid `data.json` present
- **THEN** the ingestion layer loads all draw records into an in-memory representation and reports the total count

#### Scenario: Missing dataset fails fast
- **WHEN** the service starts and `data.json` is missing or unreadable
- **THEN** ingestion fails with a clear, actionable error naming the expected path and does NOT start the dependent capabilities

### Requirement: Validate dataset schema
The ingestion layer MUST validate each draw record against the documented schema: each record has a date in `DD-MM-YYYY` format and exactly 15 numbers, each an integer in the inclusive range 1–25, with no duplicates within a single draw.

#### Scenario: Record with invalid date format is rejected
- **WHEN** a record has a date that does not match `DD-MM-YYYY`
- **THEN** validation fails, the record index is reported, and ingestion aborts

#### Scenario: Record with out-of-range number is rejected
- **WHEN** a record contains a number outside 1–25
- **THEN** validation fails, the offending record and number are reported, and ingestion aborts

#### Scenario: Record with duplicate numbers is rejected
- **WHEN** a record contains duplicate numbers within the 15-number set
- **THEN** validation fails, the offending record is reported, and ingestion aborts

#### Scenario: Record with wrong number count is rejected
- **WHEN** a record contains fewer or more than 15 numbers
- **THEN** validation fails, the offending record is reported, and ingestion aborts

### Requirement: Expose a normalized draw-history representation
The ingestion layer SHALL expose a normalized draw history to downstream capabilities with at minimum: a zero-based chronological index, an ISO-8601 date, a sorted-ascending 15-number set per draw, and the original input position. Dates MUST be converted from `DD-MM-YYYY` to ISO-8601 exactly once, at ingestion time.

#### Scenario: Downstream consumer reads normalized history
- **WHEN** a downstream capability requests the draw history
- **THEN** it receives records in chronological order with ISO-8601 dates and sorted number sets

#### Scenario: Ingestion is idempotent within a process
- **WHEN** multiple downstream capabilities request the draw history during the same process lifetime
- **THEN** they observe identical data and `data.json` is read from disk at most once

### Requirement: Report dataset provenance
The ingestion layer MUST expose dataset provenance: total draw count, date range (earliest and latest draw), source file path, and a content hash (e.g., SHA-256) of `data.json`. This provenance MUST be attached to every prediction and analysis result downstream.

#### Scenario: Provenance is queryable
- **WHEN** a caller requests dataset provenance
- **THEN** the response includes count, first date, last date, source path, and content hash

#### Scenario: Provenance round-trips to outputs
- **WHEN** a prediction or analysis is produced downstream
- **THEN** its result includes the same content hash reported by the ingestion layer
