## MODIFIED Requirements

### Requirement: Lottery number badge minimum size
Number badges representing drawn Lotofácil dezenas SHALL be rendered as filled circles with a minimum size of 40×40 px on all viewport widths. On viewports ≤ 640 px the minimum size SHALL be enforced even if it causes row wrapping.

#### Scenario: Number badges meet minimum size on mobile
- **WHEN** a draw card is rendered at 360 px viewport width
- **THEN** each number badge has a rendered width and height ≥ 40 px

#### Scenario: Number badges wrap rather than shrink
- **WHEN** 15 number badges cannot fit in a single row at the current viewport
- **THEN** badges wrap to additional rows; they do NOT scale below 40 px diameter

### Requirement: Prediction card borderless style
PredictionCard components SHALL use a borderless/ruled panel style: no explicit card border or drop-shadow. Content sections SHALL be separated by a thin 1 px rule line at reduced opacity or by vertical spacing ≥ 16 px.

#### Scenario: Prediction card has no visible box shadow
- **WHEN** a PredictionCard is rendered
- **THEN** the computed `box-shadow` is `none` and there is no `border` property producing a visible box outline

#### Scenario: Sections within card are visually separated
- **WHEN** a PredictionCard contains multiple content sections
- **THEN** sections are separated by either a `border-b` rule or a vertical gap ≥ 16 px

### Requirement: ConfidenceBadge uses design-token colors
ConfidenceBadge SHALL derive its background and text colors exclusively from the CSS design tokens (`--success`, `--warning`, `--destructive`) defined in `main.css`. Hardcoded hex or Tailwind arbitrary-value color classes SHALL NOT be used.

#### Scenario: High confidence badge uses success token
- **WHEN** a ConfidenceBadge is rendered with a high-confidence score
- **THEN** the background color matches the `--success` CSS token value

#### Scenario: Low confidence badge uses destructive token
- **WHEN** a ConfidenceBadge is rendered with a low-confidence score
- **THEN** the background color matches the `--destructive` CSS token value

### Requirement: Interactive elements minimum tap target
All interactive elements on Play pages (buttons, links, toggles) SHALL have a minimum tappable area of 44×44 px on mobile viewports (≤ 640 px). This applies to: action buttons, draw-selector options, scan trigger, and the ticket scanner.

#### Scenario: Primary action buttons meet tap target
- **WHEN** a primary Button component is rendered on a mobile viewport
- **THEN** the rendered height is ≥ 44 px
