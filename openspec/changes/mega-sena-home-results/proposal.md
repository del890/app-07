## Why

The home page currently shows only the 3 latest Lotofácil draws with no way to switch between lottery games. Users who play Mega Sena have no quick access to recent results. The navbar's "Pesquisa" button is a research-tool entry point that is not relevant as a top-level navigation item for a results-first homepage.

## What Changes

- Fetch the full Mega Sena historical draw history from a public API and save it as `mega-sena.json` at the project root, in the same format as `data.json` (Lotofácil)
- Display the 3 latest Mega Sena draws on the home page alongside the existing Lotofácil draws
- Replace the navbar's top-level navigation buttons with two game-switcher tabs: **Lotofácil** and **Mega Sena**
- The home page shows draw results for whichever game tab is active
- Remove the **Pesquisa** button from the navbar (research tool remains reachable from the Play section)

## Capabilities

### New Capabilities
- `mega-sena-data`: Historical Mega Sena draw dataset (`mega-sena.json`) in the same schema as `data.json`, plus a script/instructions to fetch/refresh it
- `game-switcher-nav`: Navbar game-switcher tabs (Lotofácil / Mega Sena) replacing the current Pesquisa/Jogar nav; active game drives the home page draw display
- `mega-sena-home-draws`: Home page fetches and displays the 3 latest Mega Sena draws (contest number, date, 6 dezenas, top prize info) using the existing Caixa API, mirroring the Lotofácil draw card structure

### Modified Capabilities
- `lotofacil-prediction-webapp`: Home page (`pages/index.vue`) gains a game-switcher state; navbar loses the Pesquisa link and gains Lotofácil / Mega Sena buttons

## Impact

- New file: `mega-sena.json` at project root (fetched script or manual data)
- `client/app/layouts/default.vue` — replace Pesquisa/Jogar nav with Lotofácil/Mega Sena game switcher tabs and update mobile bottom bar
- `client/app/pages/index.vue` — add active-game state, conditionally render Lotofácil or Mega Sena draw cards
- New composable: `client/app/composables/useLatestMegaSenaDraws.ts` — mirrors `useLatestDraws.ts` but for Mega Sena endpoint
- `client/app/types/api.ts` — add `MegaSenaDraw` type (6 dezenas, different prize tiers)
- No service/backend changes required
