## ADDED Requirements

### Requirement: Prediction numbers animate in with staggered entrance
When a prediction result is displayed, the 15 number bubbles SHALL enter the DOM with a staggered fade-and-scale transition, each bubble delayed by 30 ms relative to the previous one (leftmost first).

#### Scenario: Numbers animate on first render
- **WHEN** `isDone` becomes `true` and the prediction result is rendered
- **THEN** each number bubble fades in and scales up sequentially from left to right

#### Scenario: Re-generating clears and re-animates
- **WHEN** the user clicks Generate a second time and a new result arrives
- **THEN** the previous numbers leave and the new numbers perform the staggered entrance again

---

### Requirement: Prediction card shows a confidence meter bar
The `PredictionCard` component SHALL render a horizontal progress bar whose filled width equals `confidence × 100%`. The bar colour SHALL follow the same green / yellow / red thresholds as `ConfidenceBadge` (green ≥ 70 %, yellow ≥ 40 %, red < 40 %).

#### Scenario: High confidence renders green bar
- **WHEN** `confidence` is `0.78`
- **THEN** the bar is filled to 78 % width with a green colour

#### Scenario: Low confidence renders red bar
- **WHEN** `confidence` is `0.25`
- **THEN** the bar is filled to 25 % width with a red colour

---

### Requirement: PredictionCard is a reusable component
A `PredictionCard.vue` component SHALL accept props `numbers`, `confidence`, `explanation`, `provenance`, and optional `label`. It MUST be usable standalone so that both `next-draw.vue` (single card) and `scenario.vue` (one card per step) can use it without duplication.

#### Scenario: Scenario page renders one card per step
- **WHEN** a scenario-path prediction with `horizon: 3` is received
- **THEN** three `PredictionCard` instances are rendered, each with its respective `label` ("Draw +1", "Draw +2", "Draw +3"), numbers, confidence bar, and explanation

#### Scenario: Next-draw page renders a single card
- **WHEN** a next-draw prediction is received
- **THEN** one `PredictionCard` is rendered with no label, showing the 15 numbers, confidence bar, explanation, and provenance footer

---

### Requirement: Explanation text is displayed with readable typography
Inside `PredictionCard`, the `explanation` string SHALL be rendered in a legible body font size (≥ 14 px) with sufficient line-height (≥ 1.5) and capped at a comfortable reading width (max-w-prose or equivalent ≈ 65 ch).

#### Scenario: Long explanation wraps at reading width
- **WHEN** `explanation` contains more than 120 characters
- **THEN** the text wraps within a max-width container and does not overflow the card
