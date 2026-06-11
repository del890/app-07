## ADDED Requirements

### Requirement: Paper-ink CSS token palette
The app SHALL define a paper/ink CSS custom-property palette in `main.css`. Background SHALL be white (#ffffff), foreground near-black (~#1a1a1a), border at low-opacity ink, and muted at ~96 % lightness. Trust-blue primary SHALL be retained for interactive states.

#### Scenario: Page renders with white background
- **WHEN** the app is loaded in any browser
- **THEN** `document.body` has an effective background color of white or near-white (lightness ≥ 97%)

#### Scenario: Text is high-contrast on white
- **WHEN** body foreground text is rendered on the background
- **THEN** the contrast ratio between foreground and background tokens is ≥ 7:1

### Requirement: Roboto Mono UI-chrome typeface
The app SHALL load Roboto Mono (weights 400 and 500) via Google Fonts. Roboto Mono SHALL be applied to: navigation labels, section labels, badge text, metadata readouts, and button text. Body copy and headings SHOULD use the system sans-serif stack.

#### Scenario: Monospace font applied to nav labels
- **WHEN** the layout header nav links are rendered
- **THEN** computed `font-family` includes `Roboto Mono` or a monospace fallback

#### Scenario: Font loads with display=swap
- **WHEN** Roboto Mono is loading
- **THEN** the system monospace fallback is displayed immediately without invisible text flash

### Requirement: Tailwind token classes remain stable
The change to CSS custom-property values SHALL NOT require renaming any existing Tailwind utility class used in page or component files (e.g., `bg-background`, `text-foreground`, `border-border` remain valid).

#### Scenario: Existing class names compile without errors
- **WHEN** the Tailwind build runs after token values are changed
- **THEN** the build completes with zero errors and the token-mapped classes resolve to the updated color values
