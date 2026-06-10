## Why

The current home page is a static navigation placeholder that offers no immediate value to users. Replacing it with live draw results makes the app useful from the first screen — users can quickly see recent outcomes without navigating deeper.

## What Changes

- Remove the static hero/navigation layout from `pages/index.vue`
- Add a new home page that fetches and displays the **3 most recent Lotofácil draw results** via the official Caixa lotteries public API (`loteriascaixa-api.herokuapp.com`)
- Show for each draw: contest number, date, the 15 drawn numbers, prize tiers (winners and value), and whether the prize accumulated
- Add a new composable `useLatestDraws` to fetch the draws from the external API
- Retain navigation links to Research and Play modes as secondary actions

## Capabilities

### New Capabilities

- `latest-draws-home`: Home page that displays the 3 most recent Lotofácil draw results fetched from the public Caixa API, showing numbers, prizes and accumulation status for each draw

### Modified Capabilities

<!-- No existing spec-level requirements are changing -->

## Impact

- **`client/app/pages/index.vue`** — replaced entirely
- **`client/app/composables/useLatestDraws.ts`** — new composable (no service dependency; calls external API directly from the client)
- **`client/app/types/api.ts`** — new `LatestDraw` and `DrawPremio` interfaces for the external API response shape
- **External dependency**: `https://loteriascaixa-api.herokuapp.com/api/lotofacil/latest` and `https://loteriascaixa-api.herokuapp.com/api/lotofacil/{concurso}` — public, no auth required
- No backend/service changes needed
