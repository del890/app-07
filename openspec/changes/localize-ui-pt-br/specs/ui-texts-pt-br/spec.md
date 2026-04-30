## ADDED Requirements

### Requirement: All UI text in Portuguese (pt-BR)
Every user-visible string rendered by the client application SHALL be written in Portuguese (pt-BR). This includes navigation labels, page headings, body copy, button captions, disclaimer banners, error messages, empty-state messages, and `<title>` tags. English strings SHALL NOT appear in any rendered UI surface.

#### Scenario: Navigation bar displays Portuguese labels
- **WHEN** the user views any page
- **THEN** the top navigation shows "Pesquisa", "Jogar", and "Admin" (not "Research", "Play", "Admin")

#### Scenario: Disclaimer banner is in Portuguese
- **WHEN** the user views any page
- **THEN** the amber disclaimer banner reads a Portuguese equivalent of the research/entertainment warning

#### Scenario: Footer is in Portuguese
- **WHEN** the user views any page
- **THEN** the footer reads a Portuguese version of the tool credit line

### Requirement: Canonical glossary applied consistently
A fixed set of Portuguese terms SHALL be used uniformly across all UI files to ensure consistent terminology. The canonical mapping is:

| English term | Portuguese (pt-BR) |
|---|---|
| Research | Pesquisa |
| Play | Jogar |
| Draw | Sorteio |
| Prediction | Previsão |
| Frequency | Frequência |
| History | Histórico |
| Scan | Escanear / Digitalizar |
| Ticket | Volante |
| Scenario | Cenário |
| Next Draw | Próximo Sorteio |
| My Draw | Meu Volante |
| Suggest | Sugerir |
| Calibration | Calibração |
| Signal | Sinal |
| Structural | Estrutural |
| Order | Ordem |
| Correlation | Correlação |
| Alignment | Alinhamento |
| Hot / Cold | Quente / Frio |
| Co-occurrence | Co-ocorrência |

#### Scenario: Research navigation cards use canonical terms
- **WHEN** the user views `/research`
- **THEN** each card label matches the canonical Portuguese term for its analysis type

#### Scenario: Play mode buttons use canonical terms
- **WHEN** the user views `/play`
- **THEN** the action buttons read "Sugerir Próximo Sorteio", "Caminho de Cenário", "Meu Volante", and "Histórico"

### Requirement: Page titles (browser tab) in Portuguese
Every page that calls `useHead({ title: ... })` SHALL set a Portuguese title string.

#### Scenario: Scan page has Portuguese browser title
- **WHEN** the user navigates to the scan page
- **THEN** the browser tab title is in Portuguese (e.g., "Escanear Volante — Lotofácil")

### Requirement: Error and status messages in Portuguese
All error strings returned to the user via reactive state (e.g., `err.value`, inline status text) SHALL be written in Portuguese.

#### Scenario: Failed API call shows Portuguese error
- **WHEN** a network request to the service fails
- **THEN** the displayed error message is in Portuguese (e.g., "Falha ao carregar sorteios")
