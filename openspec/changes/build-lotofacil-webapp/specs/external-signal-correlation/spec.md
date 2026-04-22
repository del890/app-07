## ADDED Requirements

### Requirement: Ingest external world signals from pluggable sources
The system SHALL ingest external signal series from pluggable sources — at minimum: a file-based CSV/JSON signal loader, and a stub interface for future live sources (market data, earth-position / astronomy, historical world-events calendars). Each signal series MUST have a name, a sampling cadence (daily, weekly, event-keyed), a unit, a source description, and a date-indexed value stream.

#### Scenario: Register a file-based signal
- **WHEN** a caller registers a signal series via the file-based loader with a CSV of (date, value) rows
- **THEN** the system stores the series with its metadata and exposes it for correlation queries

#### Scenario: Signal metadata is mandatory
- **WHEN** a signal is registered without a name, cadence, unit, or source description
- **THEN** registration fails with a validation error identifying the missing field

### Requirement: Align signals to draw timeline
Signals MUST be aligned to the draw timeline before any correlation is computed, using a documented alignment policy (forward-fill for slower cadences, event-keyed join for calendar signals, explicit leading/lagging window controls). The alignment policy for a given correlation MUST be reported with the result.

#### Scenario: Align daily market signal to draws
- **WHEN** a daily market signal is correlated against draws
- **THEN** each draw is matched to the most recent signal value on or before its date, and the policy "forward-fill, lag 0" is reported with the result

#### Scenario: Configurable lag
- **WHEN** a caller specifies a lag of +N draws
- **THEN** the signal value at draw T is joined against draw T+N and the lag is reported in the result

### Requirement: Compute correlation with explicit significance
The system MUST compute correlation between a signal series and a draw-derived metric (e.g., draw sum, specific-number appearance, pair co-occurrence indicator) using documented statistical tests, and return both an effect-size estimate and a p-value (or confidence interval). Correlations without a reported significance indicator MUST NOT be returned.

#### Scenario: Correlation query returns effect and significance
- **WHEN** a caller requests correlation between a signal and a draw metric
- **THEN** the response includes the test used, the effect estimate, a significance indicator, and the sample size

#### Scenario: Under-powered correlation is flagged, not hidden
- **WHEN** the aligned sample size is below a documented minimum
- **THEN** the response is returned with an explicit `under_powered: true` flag rather than being suppressed or silently rounded

### Requirement: Guard against multiple-comparisons inflation
When a caller runs correlations across many signals or many draw metrics in one batch, the system SHALL apply and report a multiple-comparisons correction (e.g., Benjamini–Hochberg FDR) and clearly distinguish raw p-values from corrected ones.

#### Scenario: Batch correlation applies correction
- **WHEN** a caller runs correlations for M signals against K metrics in one batch
- **THEN** each row includes both the raw p-value and the corrected q-value, and the correction method is reported

#### Scenario: Single-correlation calls do not silently inflate
- **WHEN** a single correlation is requested without a batch context
- **THEN** the system returns the raw p-value only and does not fabricate a corrected value

### Requirement: Research artifacts must be labeled, not presented as predictions
Outputs from this capability are research artifacts, not predictions. Every response MUST carry a label indicating this, and MUST NOT be exposed to the UI's "play" surface as a prediction without going through the prediction engine.

#### Scenario: Correlation result is labeled as research
- **WHEN** any correlation result is returned
- **THEN** the response includes an `artifact_type: "research"` label and a disclaimer that correlation is not causation

### Requirement: Provenance on every correlation result
Every correlation result MUST include: signal name and source, alignment policy, draw-metric definition, dataset content hash, test used, sample size, effect estimate, raw p-value, corrected q-value (if applicable), and the timestamp of computation.

#### Scenario: Result includes full provenance
- **WHEN** a correlation result is returned
- **THEN** the result includes every field listed in this requirement
