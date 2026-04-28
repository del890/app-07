## ADDED Requirements

### Requirement: User can select exactly 15 numbers from a 25-number grid
The play section SHALL provide a `/play/my-draw` page featuring a grid of all 25 Lotofácil numbers (1–25). The user MUST be able to toggle each number on or off. The submit action MUST be disabled until exactly 15 numbers are selected, mirroring the official Lotofácil play rules.

#### Scenario: Submit is disabled with fewer than 15 numbers selected
- **WHEN** the user has selected fewer than 15 numbers
- **THEN** the submit button is disabled and a counter shows how many more numbers are needed

#### Scenario: Submit is disabled with more than 15 numbers selected
- **WHEN** the user has selected more than 15 numbers
- **THEN** the submit button is disabled and the UI indicates the excess count

#### Scenario: Submit is enabled with exactly 15 numbers selected
- **WHEN** exactly 15 numbers are selected
- **THEN** the submit button becomes active and the user can request their draw profile

### Requirement: Return a statistical profile for the user's selected draw
After submission, the service SHALL return a draw profile via `POST /v1/stats/draw-profile` containing: per-number frequency rank and historical count for each of the 15 selected numbers; pairwise co-occurrence counts for all pairs within the selection; and structural metrics for the combination (sum, even/odd count, quintile distribution, and range).

#### Scenario: Draw profile returns per-number frequency
- **WHEN** the user submits 15 numbers
- **THEN** the response includes for each number its historical appearance count and its frequency rank among all 25 numbers

#### Scenario: Draw profile returns pairwise co-occurrence
- **WHEN** the user submits 15 numbers
- **THEN** the response includes co-occurrence counts for every pair in the selection, identifying the strongest and weakest pairs

#### Scenario: Draw profile returns structural metrics
- **WHEN** the user submits 15 numbers
- **THEN** the response includes the sum, even/odd count, quintile breakdown, and min-max range for the selected combination

### Requirement: Inform the user if their draw already exists in the dataset
If the user's exact 15-number combination (as a sorted set) matches any historical draw record, the service MUST include a `dataset_match` object in the draw-profile response identifying the matching draw's date and original ID. If no match exists, `dataset_match` MUST be `null`.

#### Scenario: Exact historical match is detected and surfaced
- **WHEN** the user submits a combination that is identical to a draw already in the dataset
- **THEN** the response includes the matching draw's date and ID, and the client displays a clear match banner

#### Scenario: No match found when combination is new
- **WHEN** the user submits a combination not present in the dataset
- **THEN** `dataset_match` is `null` and the client does not display a match banner

### Requirement: Display the draw profile results in the client
The `/play/my-draw` page SHALL present the draw-profile response in a structured result panel showing: the selected numbers highlighted on the grid, per-number frequency bars or indicators, the top-N strongest co-occurring pairs, structural summary (sum, even/odd, quintiles), and — if applicable — the dataset-match banner with the matching draw's date.

#### Scenario: Result panel renders after successful submission
- **WHEN** the draw-profile API returns successfully
- **THEN** the result panel appears below the grid with all profile sections populated

#### Scenario: Dataset match banner is shown prominently
- **WHEN** the API response includes a non-null `dataset_match`
- **THEN** a highlighted banner appears at the top of the result panel with the matching draw's date and a label such as "This draw was played on <date>"

#### Scenario: No match state shows neutral message
- **WHEN** `dataset_match` is null
- **THEN** the result panel shows "This combination has not been drawn before" without a banner

### Requirement: My Draw is accessible from the play index
The `/play` index page MUST include a navigation link to `/play/my-draw` alongside the existing "Suggest Next Draw", "Scenario Path", and "History" links.

#### Scenario: My Draw link is visible on the play index
- **WHEN** the user opens `/play`
- **THEN** a "My Draw" link is visible and navigates to `/play/my-draw`
