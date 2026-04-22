## ADDED Requirements

### Requirement: Produce next-draw probability distribution
The system SHALL produce, for every number 1–25, a probability of appearing in the next draw, forming a distribution over the 25 numbers. The distribution MUST be produced by a documented ensemble of models (at minimum: a frequency/recency baseline and one learned model) and MUST be reproducible given the same dataset hash and model version.

#### Scenario: Baseline-plus-learned ensemble produces distribution
- **WHEN** a caller requests a next-draw distribution
- **THEN** the system returns 25 probabilities summing to the expected value (15, since 15 numbers are drawn), plus the ensemble composition and model versions used

#### Scenario: Same input, same output
- **WHEN** a caller requests a next-draw distribution twice with the same dataset hash and model version
- **THEN** the two responses are bit-identical (up to floating-point tolerance)

### Requirement: Produce 15-number suggestion sets with confidence
The engine MUST be able to convert a next-draw distribution into one or more 15-number suggestion sets suitable for play, each accompanied by a calibrated confidence score on a documented 0–1 scale and a human-readable explanation of which factors drove the selection.

#### Scenario: Single suggestion with confidence
- **WHEN** a caller requests a single 15-number suggestion for the next draw
- **THEN** the response includes the 15 numbers, a confidence score in [0, 1], and a concise explanation

#### Scenario: Multiple diverse suggestions
- **WHEN** a caller requests K diverse suggestions
- **THEN** the response includes K sets with pairwise diversity above a documented threshold, each with its own confidence and explanation

### Requirement: Generate self-consistent multi-draw scenario paths
The engine SHALL generate "scenario paths" — sequences of predicted draws over a caller-specified horizon H — such that each step conditions on the previous predicted steps (self-consistency), not just on the historical data. Every scenario path MUST carry a path-level confidence score.

#### Scenario: Scenario path conditions on prior predictions
- **WHEN** a caller requests a scenario path of length H
- **THEN** the system returns H predicted draws where draw t+1 was conditioned on the predicted state through draw t, and the conditioning chain is recorded in the result

#### Scenario: Scenario path carries path confidence
- **WHEN** a scenario path is returned
- **THEN** the result includes a path-level confidence score in [0, 1] that is monotonically non-increasing with horizon length (longer paths are never more confident than shorter prefixes)

### Requirement: Agent-driven meta-layer composes models and explains outputs
An LLM-powered agent MUST orchestrate the engine: it selects which underlying models and signal inputs to consult for a given query, composes their outputs, and produces the final explanation attached to every prediction. The agent MUST operate via a tool-use loop (not free-form prose generation) and call only typed, validated tools.

#### Scenario: Agent uses tools, not prose, to compute numbers
- **WHEN** the agent produces a prediction
- **THEN** every numeric value in the output traces back to a tool call against ingestion, statistical-analysis, external-signal-correlation, or a prediction model — never to free-form LLM text

#### Scenario: Agent output includes its tool trace
- **WHEN** a prediction is returned
- **THEN** the response includes the ordered list of tool calls the agent executed, with inputs, outputs, and timing

### Requirement: Calibrate and report confidence honestly
Confidence scores MUST be calibrated against a held-out slice of the historical data and re-calibrated when models or signals change. The calibration curve (reliability diagram data) MUST be stored and exposed on request.

#### Scenario: Calibration metadata is queryable
- **WHEN** a caller requests engine calibration status
- **THEN** the response includes the last calibration timestamp, the held-out window, and the reliability-curve data

#### Scenario: Uncalibrated engine refuses to produce play-surface output
- **WHEN** calibration has never been run or is marked stale
- **THEN** the engine still returns research-surface predictions labeled as uncalibrated, but refuses to serve a play-surface suggestion

### Requirement: No false certainty
The engine MUST NOT return outputs without a confidence score, MUST NOT expose a confidence of exactly 1.0, and MUST attach a persistent disclaimer that predictions are probabilistic and for research/entertainment.

#### Scenario: Missing confidence is a bug, not a feature
- **WHEN** any engine response is serialized
- **THEN** validation fails if `confidence` is null, missing, ≥ 1.0, or ≤ 0

### Requirement: Provenance on every prediction
Every engine response MUST include: dataset content hash, model versions used, agent version / prompt hash, tool trace, confidence, and timestamp.

#### Scenario: Result includes full provenance
- **WHEN** a prediction is returned
- **THEN** the response includes every field listed in this requirement
