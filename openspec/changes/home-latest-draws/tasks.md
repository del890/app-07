## 1. Types

- [x] 1.1 Add `DrawPremio` interface to `client/app/types/api.ts` (fields: `descricao`, `faixa`, `ganhadores`, `valorPremio`)
- [x] 1.2 Add `LatestDraw` interface to `client/app/types/api.ts` (fields: `concurso`, `data`, `dezenas`, `dezenasOrdemSorteio`, `premiacoes`, `acumulou`, `proximoConcurso`, `dataProximoConcurso`, `valorEstimadoProximoConcurso`)

## 2. Composable

- [x] 2.1 Create `client/app/composables/useLatestDraws.ts`
- [x] 2.2 Implement fetch of `/api/lotofacil/latest` from `https://loteriascaixa-api.herokuapp.com`
- [x] 2.3 Implement parallel fetch of the two preceding draws using `Promise.all` with `concurso - 1` and `concurso - 2`
- [x] 2.4 Return `{ draws, pending, error }` with draws sorted descending by `concurso`

## 3. Home Page

- [x] 3.1 Replace the static content in `client/app/pages/index.vue` with the new layout
- [x] 3.2 Call `useLatestDraws` and render skeleton cards while `pending` is true
- [x] 3.3 Render an error state with a retry button when `error` is set
- [x] 3.4 Render one card per draw showing: contest number, formatted date, all 15 numbers as badges, top prize (15 acertos) winner count and formatted prize value
- [x] 3.5 Show "Acumulou" indicator badge on cards where `acumulou` is true
- [x] 3.6 Add navigation links to `/research` and `/play` below the draw cards
