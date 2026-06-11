## ADDED Requirements

### Requirement: mega-sena.json static dataset
The project SHALL include a `mega-sena.json` file at the repository root containing all historical Mega Sena draw records in the same top-level schema as `data.json`:
```
{ "allowed_numbers": [...], "dataset": [{ "id", "date", "numbers" }] }
```
`allowed_numbers` SHALL be `[1..60]`. Each record's `numbers` SHALL be an array of 6 integers sorted ascending. `date` SHALL be formatted `DD-MM-YYYY`.

#### Scenario: File exists with correct structure
- **WHEN** `mega-sena.json` is read at the project root
- **THEN** it contains an object with `allowed_numbers` (array of integers 1–60) and `dataset` (array of objects each with `id`, `date`, and `numbers` of length 6)

#### Scenario: Numbers are within allowed range
- **WHEN** any record in `mega-sena.json` is inspected
- **THEN** all values in `numbers` are integers between 1 and 60 inclusive

### Requirement: Fetch script for mega-sena.json
A Node.js script at `client/scripts/fetch-mega-sena.js` SHALL fetch the full Mega Sena draw history from `https://loteriascaixa-api.herokuapp.com/api/megasena` and write `mega-sena.json` to the project root in the required format.

#### Scenario: Script produces valid JSON file
- **WHEN** the script is run with `node client/scripts/fetch-mega-sena.js`
- **THEN** `mega-sena.json` is written at the project root with the correct structure and at least 2500 records
