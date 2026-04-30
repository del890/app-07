## ADDED Requirements

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

#### Scenario: Preview image matches capture dimensions
- **WHEN** the preview image is displayed
- **THEN** it SHALL occupy the same container dimensions as the live camera viewfinder

#### Scenario: Object URL is revoked on exit
- **WHEN** the user leaves the preview view (via Retake, Confirm, or page navigation)
- **THEN** the object URL created for the preview image SHALL be revoked to free memory
