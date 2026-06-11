## ADDED Requirements

### Requirement: Paper-ink sticky header
The app SHALL render a sticky top header with a white/paper background, a 1 px bottom border at reduced opacity, and a monospace title. The header MUST remain visible and unobscured at viewport widths ≥ 320 px.

#### Scenario: Header stays visible on scroll
- **WHEN** the user scrolls the page down past the viewport height
- **THEN** the header remains fixed at the top with `position: sticky; top: 0`

#### Scenario: Header is readable at 360 px
- **WHEN** the viewport is 360 px wide
- **THEN** the title and nav links are fully visible with no text overflow or horizontal scroll

### Requirement: Minimal footer
The app SHALL render a single-line footer with a paper background, muted border-top, and muted-foreground text. The footer MUST NOT use gradient backgrounds.

#### Scenario: Footer renders without gradient
- **WHEN** any page is loaded
- **THEN** the footer background is the paper/white token color with no CSS gradient applied

### Requirement: Main content safe area
The app SHALL ensure the main content area adds sufficient bottom padding when the mobile bottom nav is visible, so content is not hidden behind the tab bar.

#### Scenario: Content not obscured by bottom tab bar
- **WHEN** the viewport is ≤ 640 px and the bottom nav is rendered
- **THEN** the main content area has bottom padding ≥ 60 px so the last content element is reachable by scrolling

### Requirement: Play-only disclaimer notice
The disclaimer about statistical analysis and responsible play SHALL appear only on Play-section pages, rendered as a compact inline notice — not as a full-width sticky banner on every page.

#### Scenario: Disclaimer absent on Research pages
- **WHEN** the user navigates to any `/research` route
- **THEN** no disclaimer banner is rendered

#### Scenario: Disclaimer present on Play pages
- **WHEN** the user navigates to any `/play` route
- **THEN** a compact disclaimer text is visible within the page content area
