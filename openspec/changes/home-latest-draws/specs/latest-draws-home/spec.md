## ADDED Requirements

### Requirement: Home page displays latest 3 draws
The home page SHALL fetch and display the 3 most recent Lotofácil draw results from the public Caixa API. Each draw card SHALL show: contest number (`concurso`), draw date, the 15 drawn numbers in sorted order, the top prize tier (15 acertos) winner count and prize value, and whether the grand prize accumulated (`acumulou`).

#### Scenario: Draws load successfully
- **WHEN** the user navigates to the home page (`/`)
- **THEN** 3 draw result cards are displayed, ordered from most recent to oldest

#### Scenario: Each card shows required fields
- **WHEN** a draw card is rendered
- **THEN** it shows the contest number, formatted date (DD/MM/YYYY), all 15 numbers as styled badges, and the top prize winner count and value

#### Scenario: Accumulated draw is highlighted
- **WHEN** a draw result has `acumulou: true`
- **THEN** the card displays an "Acumulou" indicator

#### Scenario: Loading state shown during fetch
- **WHEN** the page is loading draw data from the API
- **THEN** skeleton placeholder cards are displayed instead of empty content

#### Scenario: Error state shown on API failure
- **WHEN** the external API request fails
- **THEN** an error message is displayed with a retry button; the rest of the page (navigation links) remains accessible

### Requirement: Navigation links retained on home page
The home page SHALL continue to provide navigation links to the Research (`/research`) and Play (`/play`) sections as secondary actions below the draw results.

#### Scenario: Navigation links visible
- **WHEN** the user is on the home page
- **THEN** both "Modo Pesquisa" and "Modo Jogar" buttons are visible below the draw cards

### Requirement: Latest draws composable
A `useLatestDraws` composable SHALL encapsulate fetching the 3 most recent draws. It SHALL fetch `/api/lotofacil/latest` first, then fetch the two preceding draws in parallel using the returned `concurso` number. It SHALL expose `draws` (array of 3), `pending` (boolean) and `error`.

#### Scenario: Three draws returned in order
- **WHEN** the composable resolves successfully
- **THEN** `draws` contains exactly 3 items sorted by `concurso` descending (newest first)

#### Scenario: Parallel fetch of preceding draws
- **WHEN** the latest draw is fetched and its `concurso` is N
- **THEN** draws N-1 and N-2 are fetched concurrently in a single Promise.all call
