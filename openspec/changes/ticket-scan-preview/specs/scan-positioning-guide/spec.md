## ADDED Requirements

### Requirement: Ticket positioning guide displayed on scan page
The scan page SHALL display a positioning guide with visual examples showing how to correctly align a Lotofácil ticket before capturing.

#### Scenario: Guide is visible before capture begins
- **WHEN** the user navigates to the scan page
- **THEN** the positioning guide SHALL be visible above the camera viewfinder without any additional interaction

#### Scenario: Guide shows a correct alignment example
- **WHEN** the positioning guide is displayed
- **THEN** at least one example SHALL illustrate the ticket placed flat, well-lit, and filling the guide rectangle

#### Scenario: Guide shows an incorrect alignment example
- **WHEN** the positioning guide is displayed
- **THEN** at least one example SHALL illustrate an incorrect position (e.g. steep angle, partial crop, or obscured numbers) clearly marked as wrong

#### Scenario: Guide uses inline SVG illustrations
- **WHEN** the scan page is loaded
- **THEN** the guide illustrations SHALL be rendered as inline SVG with no external image requests

#### Scenario: Guide does not obstruct the camera viewfinder
- **WHEN** the camera is active
- **THEN** the positioning guide SHALL be placed outside the camera preview area so it does not cover the live viewfinder or the capture button
