## MODIFIED Requirements

### Requirement: Claude Vision detects marked numbers
The service SHALL send the uploaded image to the Anthropic API using a vision-capable model. The request SHALL include two image blocks: (1) the blank reference ticket image (loaded from `_process/lotofacil-bilhete.webp` at service startup and cached) and (2) the user's uploaded photo. The prompt SHALL instruct the model to identify cells that differ between the blank template and the filled photo.

The prompt SHALL include an explicit position-to-number mapping table for every cell in the 5×5 grid so the model can locate numbers by cell coordinate rather than by reading occluded printed digits. The mapping is:

```
Row\Col  C1   C2   C3   C4   C5
Row 1    21   16   11   06   01
Row 2    22   17   12   07   02
Row 3    23   18   13   08   03
Row 4    24   19   14   09   04
Row 5    25   20   15   10   05
```

The model response SHALL be parsed into an array of integer arrays as before.

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

#### Scenario: Reference image unavailable at startup
- **WHEN** `_process/lotofacil-bilhete.webp` is missing or unreadable at service startup
- **THEN** the service SHALL log a warning and fall back to the single-image call (prior behaviour)
- **THEN** the endpoint SHALL remain operational
