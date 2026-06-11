## MODIFIED Requirements

### Requirement: Lottery number badge minimum size
Number badges representing drawn dezenas SHALL be rendered as filled circles with a minimum size of 40×40 px on all viewport widths. This requirement applies to both Lotofácil (15 numbers) and Mega Sena (6 numbers) draw cards.

#### Scenario: Mega Sena number badges meet minimum size on mobile
- **WHEN** a Mega Sena draw card is rendered at 360 px viewport width
- **THEN** each of the 6 number badges has a rendered width and height ≥ 40 px

#### Scenario: Lotofácil number badges remain 40 px on mobile
- **WHEN** a Lotofácil draw card is rendered at 360 px viewport width
- **THEN** each number badge has a rendered width and height ≥ 40 px
