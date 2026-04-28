## ADDED Requirements

### Requirement: Scan route accessible from play section
The application SHALL provide a `/play/scan` page reachable from the play section. The My Draw page SHALL include an "Import from scan" button that navigates to `/play/scan`.

#### Scenario: Navigate to scan from My Draw
- **WHEN** the user is on `/play/my-draw` and clicks "Import from scan"
- **THEN** the browser SHALL navigate to `/play/scan`

#### Scenario: Scan page renders within play layout
- **WHEN** the user navigates directly to `/play/scan`
- **THEN** the page SHALL render within the default layout and display the `TicketScanner` component
