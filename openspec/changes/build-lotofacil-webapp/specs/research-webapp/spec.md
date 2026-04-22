## ADDED Requirements

### Requirement: Provide two top-level modes — research and play
The webapp SHALL present two distinct top-level modes: a **research** mode (rigorous pattern exploration, statistical visualizations, correlation experiments) and a **play** mode (actionable 15-number suggestions). The current mode MUST be visible in the UI at all times and MUST be reflected in the URL.

#### Scenario: Mode is visible and URL-addressable
- **WHEN** a user switches modes
- **THEN** the URL path updates to reflect the mode (e.g., `/research`, `/play`) and a persistent indicator shows the active mode

#### Scenario: Deep-link to a mode
- **WHEN** a user opens a `/research/...` or `/play/...` URL directly
- **THEN** the app loads the correct mode without flashing the other mode first

### Requirement: Confidence scores are always visible on predictions
Any prediction displayed in the UI — next-draw distribution, 15-number suggestion, or scenario path — MUST display its confidence score prominently and MUST include a plain-language explanation that predictions are probabilistic.

#### Scenario: Suggestion card shows confidence
- **WHEN** a 15-number suggestion is rendered
- **THEN** its confidence score is rendered at least as prominently as the numbers themselves, and a disclaimer is visible without scrolling

#### Scenario: Predictions with missing confidence are not rendered
- **WHEN** the API returns a prediction with no confidence field
- **THEN** the UI renders an error state for that card rather than the numbers

### Requirement: Research mode exposes statistical and correlation views
Research mode MUST provide, at minimum: a frequency view, a gap / hot-cold view, a co-occurrence (pair/triplet) explorer, a structural-distributions view (sum, even/odd, quintiles), an order-analysis view, a PI-alignment view, and an external-signal correlation explorer. Each view MUST show the dataset hash, the window in use, and — where applicable — significance indicators.

#### Scenario: Frequency view renders from the API
- **WHEN** a user opens the frequency view
- **THEN** the view calls the statistics API, renders a chart over all 25 numbers, and displays the dataset hash and window

#### Scenario: Correlation explorer requires significance
- **WHEN** a correlation row would be rendered without a p-value or q-value
- **THEN** the UI hides the numeric effect and shows "significance unavailable" instead

### Requirement: Play mode surfaces calibrated predictions only
Play mode MUST query prediction endpoints and MUST refuse to render a suggestion if the engine reports the prediction as uncalibrated or stale. In that case, the UI MUST route the user to research mode with an explanatory banner.

#### Scenario: Calibrated prediction is shown
- **WHEN** the engine returns a prediction with `calibrated: true`
- **THEN** play mode renders the suggestion with its confidence and explanation

#### Scenario: Uncalibrated engine is refused in play mode
- **WHEN** the engine returns a prediction with `calibrated: false` or missing calibration
- **THEN** play mode does NOT render the suggestion and shows a banner directing the user to research mode

### Requirement: Stream agent output where available
When prediction endpoints support SSE streaming, the webapp SHOULD stream tool calls and partial output into the UI so the user sees the agent reasoning in real time. Falling back to a single JSON response MUST be transparent to the user.

#### Scenario: Streaming renders progressively
- **WHEN** a streaming prediction is requested
- **THEN** the UI renders each tool call and partial result as events arrive and finalizes on stream close

#### Scenario: Streaming failure falls back silently
- **WHEN** the streaming connection drops
- **THEN** the UI automatically retries in non-streaming mode and surfaces a small "retried" indicator

### Requirement: Built with Nuxt and TypeScript (strict)
The client MUST be implemented with Nuxt 3+ and TypeScript in strict mode, following the project's `client-stack` skill. No plain JavaScript source files are allowed in the client.

#### Scenario: Client enforces TypeScript
- **WHEN** a `.js` source file is introduced into the client tree
- **THEN** the project's lint / type-check step fails the build

### Requirement: Responsive and accessible
The webapp MUST render usefully on mobile viewports (≥ 360px wide) and MUST meet WCAG 2.1 AA for color contrast, keyboard navigation, and focus states on all interactive controls.

#### Scenario: Mobile view
- **WHEN** the app is opened on a 360px-wide viewport
- **THEN** all primary views remain usable without horizontal scroll

#### Scenario: Keyboard-only navigation
- **WHEN** a user navigates the app using only the keyboard
- **THEN** every interactive control is reachable and shows a visible focus state

### Requirement: No user accounts and no real-money integration
The webapp MUST NOT implement user authentication, account storage, betting automation, or any real-money integration. Any UI copy MUST frame suggestions as research/entertainment, never as investment or guaranteed wins.

#### Scenario: No auth surface exists
- **WHEN** a user browses the app
- **THEN** there is no login, signup, or account page anywhere in the UI

#### Scenario: Copy remains non-promissory
- **WHEN** any suggestion is rendered
- **THEN** the surrounding copy does not use words like "guaranteed", "winning", "sure", or promise any financial outcome
