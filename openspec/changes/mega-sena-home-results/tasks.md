## 1. Mega Sena Dataset

- [x] 1.1 Create `client/scripts/fetch-mega-sena.js`: fetch all draws from `https://loteriascaixa-api.herokuapp.com/api/megasena`, transform to `{ id, date: "DD-MM-YYYY", numbers: [...sorted] }`, write `mega-sena.json` to project root with `allowed_numbers: [1..60]`
- [x] 1.2 Run the script (`node client/scripts/fetch-mega-sena.js`) and verify `mega-sena.json` is created at the project root with ≥ 2500 records in the correct format

## 2. Types

- [x] 2.1 Add `MegaSenaDraw` as a type alias for `LatestDraw` in `client/app/types/api.ts`
- [x] 2.2 Add `MegaSenaRecord` interface `{ id: number; date: string; numbers: number[] }` to `client/app/types/api.ts`

## 3. Active Game Composable

- [x] 3.1 Create `client/app/composables/useActiveGame.ts`: exports a singleton `activeGame` ref typed as `'lotofacil' | 'megasena'`, defaulting to `'lotofacil'`, and a `setActiveGame` function

## 4. Mega Sena Draw Composable

- [x] 4.1 Create `client/app/composables/useLatestMegaSenaDraws.ts`: mirrors `useLatestDraws.ts` but targets `/api/megasena/latest` and `/api/megasena/:concurso`; returns `{ draws, pending, error, retry }`

## 5. Navbar Update

- [x] 5.1 In `layouts/default.vue`, replace the desktop nav Pesquisa/Jogar links with three buttons: **Lotofácil** (calls `setActiveGame('lotofacil')`, navigates to `/`), **Mega Sena** (calls `setActiveGame('megasena')`, navigates to `/`), and **Jogar** (route link to `/play`)
- [x] 5.2 Active style for Lotofácil/Mega Sena buttons: filled (bg-foreground text-background) when their game matches `activeGame`; ghost border style otherwise. Jogar keeps its existing route-active style
- [x] 5.3 Update the mobile bottom tab bar: replace the two-tab (Pesquisa/Jogar) layout with three tabs — **Lotofácil**, **Mega Sena**, **Jogar** — each one-third width, with icons and ≥ 44 px height. Lotofácil and Mega Sena update `activeGame` and navigate to `/`; Jogar links to `/play`
- [x] 5.4 Update the header site title from "Lotofácil research" to "Loterias research" to reflect multi-game scope

## 6. Home Page Update

- [x] 6.1 In `pages/index.vue`, import `useActiveGame` and `useLatestMegaSenaDraws`; call both composables at setup so both are ready when user switches tabs (avoids delay on first switch)
- [x] 6.2 Update the section header: show "Lotofácil · Últimos Sorteios" when `activeGame === 'lotofacil'`, "Mega Sena · Últimos Sorteios" when `activeGame === 'megasena'`
- [x] 6.3 Conditionally render the correct draw cards using `v-if="activeGame === 'lotofacil'"` / `v-else` — the Mega Sena block uses 6-badge cards (same `w-10 h-10 rounded-full bg-primary` style) and top prize from `faixa === 1` with label "6 acertos"
- [x] 6.4 Loading skeleton: when Mega Sena is active and pending, show 3 skeleton cards with 6 badge placeholders each (instead of 15)
- [x] 6.5 Remove the bottom navigation links ("Modo Pesquisa" / "Modo Jogar" buttons) from the page — game switching is now handled by the navbar

## 7. Build Verification

- [x] 7.1 Run `npm run build` in `client/` and confirm zero errors
- [x] 7.2 Start dev server and verify: default load shows Lotofácil draws; clicking Mega Sena tab shows 6-number Mega Sena draws; clicking Jogar navigates to `/play`; no Pesquisa link is visible anywhere in the header
