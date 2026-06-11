## Context

The app is a Nuxt 3 / TypeScript SPA that currently:
- Shows 3 latest Lotofácil draws on `pages/index.vue` via `useLatestDraws` which calls `https://loteriascaixa-api.herokuapp.com/api/lotofacil/latest` and the two preceding concursos
- Has a sticky header with Pesquisa and Jogar nav links (desktop) + a mobile bottom tab bar
- `data.json` at the project root holds the full Lotofácil history; format: `{ allowed_numbers, dataset: [{id, date, numbers}] }`
- The Caixa public API (`loteriascaixa-api.herokuapp.com`) also exposes `/api/megasena/latest` and `/api/megasena/:concurso` with the same `LatestDraw` response shape (concurso, data, dezenas, premiacoes, acumulou)

## Goals / Non-Goals

**Goals:**
- Produce `mega-sena.json` at project root with all historical Mega Sena draws in the `data.json` schema
- Add `useLatestMegaSenaDraws` composable parallel to `useLatestDraws`
- Add `MegaSenaDraw` type (Mega Sena has 6 numbers from 1–60, different prize faixas)
- Replace the navbar Pesquisa/Jogar links with Lotofácil/Mega Sena game-switcher tabs
- Update mobile bottom bar to match: Lotofácil tab and Mega Sena tab
- `pages/index.vue` reactively shows the correct draw cards based on the active game

**Non-Goals:**
- Deep Mega Sena research/statistics pages (the research routes remain Lotofácil-only)
- Offline caching or service-worker strategies
- Authenticating or rate-limiting the public API
- Automatic `mega-sena.json` refresh pipeline

## Decisions

### D1 — Game switcher lives in the navbar, drives index page via URL query/state

**Decision:** The active game is tracked as a reactive ref `activeGame: 'lotofacil' | 'megasena'` in a composable `useActiveGame`. The navbar buttons update this value; `pages/index.vue` reads it to decide which draw set to show.

Using a composable (not a URL query param) keeps the URL clean (`/`) and avoids a full page navigation on tab switch.

**Alternative considered:** Two separate routes (`/lotofacil`, `/megasena`) — rejected because it adds routing complexity and breaks existing deep links.

---

### D2 — `mega-sena.json` fetched via a one-off Node script

**Decision:** Provide a `scripts/fetch-mega-sena.js` Node script that hits the Caixa API in batches and writes `mega-sena.json`. The file is committed to the repo. The script is re-run manually when a refresh is needed.

**Rationale:** Consistent with how `data.json` is maintained (static file). No runtime dependency on the bulk history endpoint.

**Alternative considered:** Fetching all history at runtime — rejected because the API has thousands of records and would be slow/rate-limited.

---

### D3 — Reuse `LatestDraw` type for Mega Sena live fetch; separate `MegaSenaDraw` for static JSON

**Decision:** The live fetch composable (`useLatestMegaSenaDraws`) uses the same `LatestDraw` interface (already matches the API shape for both games). A separate lightweight `MegaSenaRecord` type mirrors `LotofacilRecord` for the static JSON.

**Rationale:** Avoids duplicating the full `LatestDraw` interface while still having a typed representation for the static dataset.

---

### D4 — Navbar: remove Pesquisa, add Lotofácil + Mega Sena, keep Jogar accessible

**Decision:** The desktop nav shows: `Lotofácil` | `Mega Sena` | `Jogar`. "Pesquisa" is removed. The mobile bottom bar shows: `Lotofácil` | `Mega Sena` | `Jogar` (three tabs).

Lotofácil and Mega Sena are game-switcher buttons (update `activeGame`, navigate to `/`). Jogar remains a route link to `/play`.

**Rationale:** Jogar is still a primary action; removing it would break discoverability of the prediction features.

---

### D5 — Draw card component parameterised for number count

**Decision:** The draw number badges on `index.vue` are rendered inline (no separate component needed). A `v-if` on `activeGame` switches between the Lotofácil card loop (15 badges) and the Mega Sena card loop (6 badges). The existing badge styling (`w-10 h-10 rounded-full bg-primary`) applies to both.

## Risks / Trade-offs

- **[Risk] Caixa API shape differs slightly for Mega Sena** → Verify `dezenas` count (should be 6) and `premiacoes` faixa 1 label. The `LatestDraw` interface is flexible enough; worst case we cast.
- **[Risk] `useActiveGame` state resets on hard-refresh** → Acceptable; the default is Lotofácil which is the existing experience. Could persist to `localStorage` as a future enhancement.
- **[Risk] fetch-mega-sena.js script may hit rate limits on the Caixa API** → Add a 200ms delay between requests and batch in chunks of 50.

## Migration Plan

1. Write `scripts/fetch-mega-sena.js` and run it to generate `mega-sena.json`
2. Add `MegaSenaRecord` type to `types/api.ts`
3. Add `useActiveGame` composable
4. Add `useLatestMegaSenaDraws` composable
5. Update `layouts/default.vue` — swap nav buttons
6. Update `pages/index.vue` — add game switcher logic and Mega Sena draw cards
7. Build and verify

## Open Questions

- Should the Jogar (play) section eventually support Mega Sena predictions? Not in scope here.
