## MODIFIED Requirements

### Requirement: Captured image preview before upload
After the user captures a frame, the system SHALL display the captured still image and present **Confirm** and **Retake** actions before uploading the image to the scan API.

#### Scenario: Preview displayed after capture
- **WHEN** the user clicks **Capture** on the scan page
- **THEN** the live camera view is replaced by a still image showing exactly what was captured
- **AND** **Confirm** and **Retake** buttons are visible

#### Scenario: Confirm sends image for analysis
- **WHEN** the user clicks **Confirm** on the preview view
- **THEN** the captured image is uploaded to the scan API
- **AND** the loading indicator is displayed while the API processes the image

#### Scenario: Retake returns to live camera
- **WHEN** the user clicks **Retake** on the preview view
- **THEN** the captured image is discarded
- **AND** the live camera viewfinder is restarted
- **AND** no API call is made

#### Scenario: Preview image container is portrait
- **WHEN** the preview image is displayed
- **THEN** the image container SHALL have a portrait aspect ratio (taller than wide, 9:16)
- **AND** it SHALL occupy the same container dimensions as the live camera viewfinder

#### Scenario: Object URL is revoked on exit
- **WHEN** the user leaves the preview view (via Retake, Confirm, or page navigation)
- **THEN** the object URL created for the preview image SHALL be revoked to free memory

## ADDED Requirements

### Requirement: Camera viewfinder uses portrait aspect ratio
The live camera viewfinder container SHALL use a portrait (9:16) aspect ratio so that the ticket alignment guide fills the majority of the visible area.

#### Scenario: Viewfinder container is taller than wide
- **WHEN** the scan page is displayed on any screen size
- **THEN** the camera viewfinder container SHALL be taller than it is wide (9:16 aspect ratio)

#### Scenario: Ticket alignment guide fills the portrait container
- **WHEN** the camera viewfinder is visible
- **THEN** the ticket guide rectangle SHALL occupy at least 70% of the container width
- **AND** the guide rectangle SHALL remain portrait-oriented (aspect-ratio 1:2.3)

#### Scenario: Stream aspect ratio hint is requested
- **WHEN** the app requests camera access via getUserMedia
- **THEN** the video constraints SHALL include an `aspectRatio: 9/16` ideal hint
