## ADDED Requirements

### Requirement: Bottom tab bar on mobile
The app SHALL render a fixed bottom navigation bar with two tabs ("Pesquisa" and "Jogar") at viewport widths ≤ 640 px. The top-nav mode-switcher links SHALL be hidden at this breakpoint.

#### Scenario: Bottom tab bar visible on 375 px viewport
- **WHEN** the viewport width is 375 px
- **THEN** a bottom tab bar is visible with two tappable areas for Research and Play

#### Scenario: Bottom tab bar hidden on desktop
- **WHEN** the viewport width is ≥ 768 px
- **THEN** the bottom tab bar is not rendered (display: none or v-if)

#### Scenario: Top nav hidden on mobile
- **WHEN** the viewport width is ≤ 640 px
- **THEN** the top-nav research/play mode links are hidden

### Requirement: Bottom tab bar active state
The active tab in the bottom tab bar SHALL be visually distinct from the inactive tab using the primary token color or a filled/underlined indicator.

#### Scenario: Active tab highlighted
- **WHEN** the user is on a `/play` route and the bottom nav is visible
- **THEN** the "Jogar" tab has a visually distinct active style (bold text, filled background, or border indicator)

### Requirement: Bottom tab safe-area inset
The bottom tab bar SHALL respect iOS safe-area insets using `padding-bottom: env(safe-area-inset-bottom)` or equivalent, preventing overlap with the iPhone home indicator.

#### Scenario: Bar clears home indicator on iOS
- **WHEN** the app is viewed on an iPhone with a home indicator (notched devices)
- **THEN** the tab bar bottom edge is padded so no interactive area is obscured by the home indicator

### Requirement: Tab touch targets
Each tab in the bottom bar SHALL have a minimum tappable area of 44×44 px.

#### Scenario: Tap targets meet minimum size
- **WHEN** each tab is rendered
- **THEN** the rendered height of each tab area is ≥ 44 px and its full width spans at least half the screen width
