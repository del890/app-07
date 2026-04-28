## MODIFIED Requirements

### Requirement: Expose a normalized draw-history representation
The ingestion layer SHALL expose a normalized draw history to downstream capabilities with at minimum: a zero-based chronological index, an ISO-8601 date, a sorted-ascending 15-number set per draw, and the original input position. Dates MUST be converted from `DD-MM-YYYY` to ISO-8601 exactly once, at ingestion time.

The ingestion module MUST additionally expose a `reload_from_settings()` function that clears the in-memory cache and reinvokes ingestion from the current `data.json` file. This function MUST be thread-safe and MUST be callable multiple times within a process lifetime without requiring a restart.

#### Scenario: Downstream consumer reads normalized history
- **WHEN** a downstream capability requests the draw history
- **THEN** it receives records in chronological order with ISO-8601 dates and sorted number sets

#### Scenario: Ingestion is idempotent within a process without reload
- **WHEN** multiple downstream capabilities request the draw history during the same process lifetime without an intervening reload
- **THEN** they observe identical data and `data.json` is read from disk at most once

#### Scenario: Hot-reload updates the in-memory history
- **WHEN** `reload_from_settings()` is called after `data.json` has been updated on disk
- **THEN** subsequent calls to `get_cached_history()` return the updated draw history reflecting the new records

#### Scenario: Concurrent reload is safe
- **WHEN** `reload_from_settings()` is called from a background task while an API request is concurrently reading `get_cached_history()`
- **THEN** the API request completes successfully using either the old or new history — partial state is never exposed
