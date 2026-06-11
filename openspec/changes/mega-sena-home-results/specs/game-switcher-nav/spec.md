## ADDED Requirements

### Requirement: Game-switcher tabs in desktop navbar
The desktop navbar SHALL replace the "Pesquisa" and "Jogar" nav links with three buttons: **Lotofácil**, **Mega Sena**, and **Jogar**. Lotofácil and Mega Sena are game-switcher buttons that update the active game and navigate to `/`. Jogar remains a route link to `/play`.

#### Scenario: Lotofácil tab is active by default
- **WHEN** the app is first loaded or navigated to `/`
- **THEN** the Lotofácil button has the active visual style (filled background)

#### Scenario: Clicking Mega Sena sets active game
- **WHEN** the user clicks the Mega Sena button
- **THEN** the Mega Sena button shows the active style and the home page switches to Mega Sena results

#### Scenario: Pesquisa button is absent
- **WHEN** the desktop navbar is rendered on any route
- **THEN** no "Pesquisa" text or link is present in the header

### Requirement: Game-switcher tabs in mobile bottom bar
The mobile bottom tab bar (≤ 640 px) SHALL show three tabs: **Lotofácil**, **Mega Sena**, and **Jogar**, replacing the previous Research/Jogar two-tab layout.

#### Scenario: Three tabs on mobile
- **WHEN** the viewport is ≤ 640 px
- **THEN** the bottom bar shows three equal-width tabs: Lotofácil, Mega Sena, Jogar

#### Scenario: Active game tab is highlighted on mobile
- **WHEN** the active game is Mega Sena and the viewport is ≤ 640 px
- **THEN** the Mega Sena mobile tab has the active visual indicator (border-t-2 or equivalent)

### Requirement: Active game state persists within session
The active game selection (Lotofácil or Mega Sena) SHALL be maintained as reactive state (`useActiveGame` composable) that persists across route changes within the same session. Default value is `'lotofacil'`.

#### Scenario: Game selection survives navigation to /play and back
- **WHEN** the user selects Mega Sena, navigates to `/play`, then returns to `/`
- **THEN** the Mega Sena tab is still active and Mega Sena draws are displayed
