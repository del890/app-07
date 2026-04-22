## ADDED Requirements

### Requirement: Compute per-number frequency statistics
The system SHALL compute, for every number 1–25, its absolute and relative frequency across the full historical draw set, and over a configurable rolling window (most recent N draws).

#### Scenario: Full-history frequency report
- **WHEN** a caller requests per-number frequency over the full dataset
- **THEN** the system returns, for each number 1–25, its count and its share of draws in which it appeared

#### Scenario: Rolling-window frequency report
- **WHEN** a caller requests per-number frequency with window size N
- **THEN** the system returns frequencies computed only over the most recent N draws and reports N in the response

### Requirement: Compute gap and hot/cold statistics
The system MUST compute, for every number, the current gap (draws since last appearance), average historical gap, maximum gap, and a derived hot/cold classification based on a documented threshold.

#### Scenario: Gap report
- **WHEN** a caller requests gap statistics
- **THEN** the response includes current gap, mean gap, and maximum gap for every number 1–25

#### Scenario: Hot/cold classification is deterministic and documented
- **WHEN** the system classifies a number as hot, neutral, or cold
- **THEN** the classification is derived from documented thresholds over current-gap-vs-mean-gap, and the same input produces the same classification

### Requirement: Compute co-occurrence statistics
The system SHALL compute co-occurrence frequencies for number pairs, triplets, and quadruplets across the full history, and expose the top-K most common combinations at each arity.

#### Scenario: Pair co-occurrence query
- **WHEN** a caller requests the top-K most common number pairs
- **THEN** the system returns K pairs ordered by co-occurrence count, with each pair's count and share of draws

#### Scenario: Triplet and quadruplet queries
- **WHEN** a caller requests top-K triplets or quadruplets
- **THEN** the system returns K combinations at the requested arity with counts and shares

### Requirement: Compute draw-level structural statistics
The system MUST compute per-draw structural statistics — sum of the 15 numbers, count of even vs odd numbers, count per quintile (1–5, 6–10, 11–15, 16–20, 21–25), and min/max — and expose their distributions across the full history.

#### Scenario: Structural distribution report
- **WHEN** a caller requests structural distributions
- **THEN** the response includes histograms (or binned counts) for sum, even/odd split, quintile distribution, and min/max

### Requirement: Compute intra-draw order analysis
The system SHALL expose order-based statistics for each draw — the sequence of numbers in the order they were originally drawn (when available) OR the sorted-ascending canonical order — and compute transition statistics between consecutive positions across history.

#### Scenario: Order is preserved per source data
- **WHEN** the source `data.json` provides original draw order
- **THEN** order statistics reflect the original order and this fact is labeled in the response

#### Scenario: Order is fallback when unavailable
- **WHEN** the source does not provide original draw order
- **THEN** order statistics use sorted-ascending canonical order and the response labels the order as canonical, not drawn

### Requirement: Compute PI-alignment analysis
The system SHALL provide a PI-alignment analysis that compares draw sequences against the digits of PI using documented alignment rules (e.g., matching number-vs-digit mappings, windowed digit-sum matches). The rules MUST be explicit, reproducible, and published alongside the result.

#### Scenario: PI alignment returns a score and explanation
- **WHEN** a caller requests PI alignment for a draw or window
- **THEN** the response includes the alignment score, the rule used, the PI digits consulted, and a clear explanation of the computation

#### Scenario: PI alignment is reproducible
- **WHEN** the same draw and same rule are re-evaluated
- **THEN** the system returns the exact same score

### Requirement: Attach confidence and provenance to every statistic
Every statistical result returned by this capability MUST carry: the dataset content hash from ingestion, the window size (or "full") used, the computation timestamp, and — for stochastic or threshold-based outputs — a documented confidence or significance indicator.

#### Scenario: Result includes provenance
- **WHEN** any statistical result is returned
- **THEN** the result includes dataset hash, window descriptor, and computation timestamp
