## ADDED Requirements

### Requirement: Latest Mega Sena draws on home page
The home page (`pages/index.vue`) SHALL display the 3 latest Mega Sena draws when the Mega Sena game tab is active. Each draw card SHALL show: contest number, date, the 6 drawn numbers as filled circle badges, and the top prize winner count and value.

#### Scenario: Mega Sena draws render when tab active
- **WHEN** the user selects the Mega Sena tab
- **THEN** exactly 3 draw cards are displayed, each with 6 number badges

#### Scenario: Number badges show 6 numbers
- **WHEN** a Mega Sena draw card is rendered
- **THEN** each card contains exactly 6 number badge elements

#### Scenario: Loading state shown while fetching
- **WHEN** the Mega Sena tab is active and draws are being fetched
- **THEN** skeleton placeholder cards are shown

#### Scenario: Error state shown on fetch failure
- **WHEN** the Mega Sena draw fetch fails
- **THEN** an error message and retry button are displayed

### Requirement: Lotofácil draws shown when Lotofácil tab active
The home page SHALL display the 3 latest Lotofácil draws (existing behavior) when the Lotofácil game tab is active.

#### Scenario: Lotofácil draws render on default load
- **WHEN** the page loads with default game (Lotofácil)
- **THEN** Lotofácil draw cards with 15 number badges each are shown

### Requirement: MegaSenaDraw type
The app SHALL define a `MegaSenaDraw` TypeScript type alias for `LatestDraw` to explicitly represent Mega Sena API responses. A `MegaSenaRecord` interface SHALL exist for static JSON dataset records.

#### Scenario: Type is usable without runtime errors
- **WHEN** the TypeScript compiler processes `useLatestMegaSenaDraws.ts`
- **THEN** there are no type errors related to Mega Sena draw data

### Requirement: useLatestMegaSenaDraws composable
A composable `useLatestMegaSenaDraws` SHALL fetch the 3 latest Mega Sena draws from `https://loteriascaixa-api.herokuapp.com/api/megasena/latest` and the two preceding concursos.

#### Scenario: Returns three sorted draws
- **WHEN** `useLatestMegaSenaDraws` resolves successfully
- **THEN** `draws` contains 3 items sorted by `concurso` descending
