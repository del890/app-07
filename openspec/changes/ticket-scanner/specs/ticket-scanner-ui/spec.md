## ADDED Requirements

### Requirement: Camera permission and initialisation
The system SHALL request camera access via `getUserMedia` when the scan page is opened. If permission is denied or `getUserMedia` is unavailable, the system SHALL fall back to a file-picker (`<input type="file" accept="image/*" capture="environment">`).

#### Scenario: Camera permission granted
- **WHEN** the user opens `/play/scan` and the browser grants camera access
- **THEN** a live video preview SHALL appear inside `TicketScanner.vue` within 2 seconds

#### Scenario: Camera permission denied
- **WHEN** the user opens `/play/scan` and the browser denies camera access
- **THEN** the live preview SHALL not appear and a file-upload button SHALL be shown instead

#### Scenario: File picker fallback used
- **WHEN** the user opens `/play/scan` on a context where `getUserMedia` is unavailable
- **THEN** a file-upload control SHALL be shown as the primary input

### Requirement: Still-frame capture and compression
The system SHALL capture a still JPEG frame from the live viewfinder when the user presses "Capture". Before uploading, the image SHALL be resized to a maximum of 1280 px on the longest side and compressed at JPEG quality 0.85 using the browser Canvas API.

#### Scenario: Capture produces a compressed image
- **WHEN** the user presses "Capture" with an active camera stream
- **THEN** an offscreen canvas SHALL render the current frame at the target resolution
- **THEN** the resulting JPEG blob SHALL not exceed 4 MB

#### Scenario: Re-capture before confirming
- **WHEN** the user presses "Retake" on the confirmation screen
- **THEN** the live viewfinder SHALL resume and the previous captured frame SHALL be discarded

### Requirement: Upload and loading state
The `useTicketScanner` composable SHALL send the captured image to `POST /v1/tickets/scan` as multipart/form-data. While the request is in-flight the UI SHALL display a loading indicator and disable the "Confirm" button.

#### Scenario: Successful upload
- **WHEN** the image is submitted and the service responds with HTTP 200
- **THEN** the loading indicator SHALL be hidden and the result screen SHALL be shown

#### Scenario: Upload error
- **WHEN** the service responds with a non-2xx status or the request fails
- **THEN** a human-readable error message SHALL be displayed
- **THEN** a "Try again" button SHALL be shown that returns to the capture screen

### Requirement: Result confirmation and editing
After a successful scan the system SHALL show each detected game set as a mini 5×5 grid with marked cells highlighted. The user SHALL be able to toggle individual numbers on/off before saving. Confirming SHALL save the first game set to `useMyDrawStore` and navigate to `/play/my-draw`.

#### Scenario: Review detected numbers
- **WHEN** the scan returns one or more game sets
- **THEN** each set SHALL be rendered as a 5-column number grid with marked cells visually distinguished

#### Scenario: Edit a number before saving
- **WHEN** the user taps/clicks a number cell on the result screen
- **THEN** the cell SHALL toggle between marked and unmarked

#### Scenario: Confirm and save
- **WHEN** the user presses "Save" on the result screen
- **THEN** the first game set's numbers SHALL be written to `useMyDrawStore`
- **THEN** the user SHALL be navigated to `/play/my-draw`

#### Scenario: Discard scan result
- **WHEN** the user presses "Discard" on the result screen
- **THEN** the stored data SHALL NOT be written and the user SHALL return to the capture screen

### Requirement: Camera stream cleanup
The system SHALL stop all camera tracks and release the `MediaStream` when the scan page is unmounted or when the user navigates away.

#### Scenario: Navigation away from scan page
- **WHEN** the user navigates to any other route
- **THEN** all active `MediaStreamTrack` instances SHALL be stopped
- **THEN** no camera indicator light SHALL remain active in the browser
