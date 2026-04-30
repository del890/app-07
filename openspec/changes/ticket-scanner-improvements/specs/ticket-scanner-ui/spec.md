## MODIFIED Requirements

### Requirement: Still-frame capture and compression
The system SHALL capture a still JPEG frame from the live viewfinder when the user presses "Capture". Before uploading, the image SHALL:
1. Be preprocessed on an offscreen canvas with a contrast filter (`contrast(180%) brightness(110%) saturate(0%)`) to make ink marks visually distinct from the paper background.
2. Be resized to a maximum of **1920 px** on the longest side (up from 1280 px).
3. Be compressed at JPEG quality 0.85.

The resulting JPEG blob SHALL not exceed 4 MB.

#### Scenario: Capture produces a preprocessed, compressed image
- **WHEN** the user presses "Capture" with an active camera stream
- **THEN** an offscreen canvas SHALL apply the contrast/grayscale filter before encoding
- **THEN** the resulting JPEG blob SHALL not exceed 4 MB
- **THEN** the image SHALL be visually higher-contrast than the raw camera frame

#### Scenario: Re-capture before confirming
- **WHEN** the user presses "Retake" on the confirmation screen
- **THEN** the live viewfinder SHALL resume and the previous captured frame SHALL be discarded

## ADDED Requirements

### Requirement: Ticket alignment guide overlay
The `TicketScanner.vue` component SHALL display a semi-transparent rectangular guide overlay centred in the live viewfinder with corner marker indicators. The overlay aspect ratio SHALL match the physical Lotofácil ticket (portrait, approximately 1:2.3). The overlay SHALL include a brief text label ("Align ticket within the guide").

#### Scenario: Guide visible during capture
- **WHEN** the camera stream is active and the viewfinder is displayed
- **THEN** the alignment guide overlay SHALL be visible on top of the video feed
- **THEN** the overlay SHALL NOT obscure the "Capture" button

#### Scenario: Guide hidden after capture
- **WHEN** the user has captured a frame and the result is being reviewed
- **THEN** the alignment overlay SHALL NOT be displayed
