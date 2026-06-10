## Context

The current home page (`pages/index.vue`) is a static navigation screen with a headline and two buttons — it provides no live content. The app targets Lotofácil players who want immediate insight into recent outcomes. The public Caixa API (`loteriascaixa-api.herokuapp.com`) is available without authentication and returns structured draw results.

## Goals / Non-Goals

**Goals:**
- Fetch and display the 3 most recent Lotofácil draws on the home page
- Show the drawn numbers, contest number, date, prize tiers and accumulation status for each draw
- Keep navigation to Research and Play modes visible
- Fetch data client-side only (no service/backend involvement)

**Non-Goals:**
- Caching or persisting draw results locally (IndexedDB, pinia store)
- Historical browsing beyond the 3 latest draws
- Real-time polling or WebSocket updates
- Modifying the backend service

## Decisions

### D1 — Use `loteriascaixa-api.herokuapp.com` as the data source

The official Caixa endpoint (`servicebus.caixa.gov.br`) requires CORS setup and is frequently blocked in browsers. The community proxy `loteriascaixa-api.herokuapp.com` returns the same structured data, is CORS-friendly, and requires no authentication.

**Alternatives considered:**
- Scraping `loteriasonline.caixa.gov.br` — HTML scraping is brittle and prone to breaking on layout changes
- Routing through the backend service — adds latency, infrastructure coupling, and maintenance burden for a simple read-only display

### D2 — Fetch strategy: `/latest` then two preceding draws by contest number decrement

`GET /api/lotofacil/latest` returns the most recent draw including `concurso` (the contest number). The two preceding draws are fetched in parallel via `GET /api/lotofacil/{concurso - 1}` and `GET /api/lotofacil/{concurso - 2}`. This is reliable because Lotofácil contest numbers are strictly sequential.

**Alternatives considered:**
- Calling a hypothetical `/latest?count=3` endpoint — does not exist in this API
- Sequential fetches — slower; parallel fetches complete in one round-trip

### D3 — New composable `useLatestDraws` isolates external API logic

The composable returns `{ draws, pending, error }` using `useFetch`/`useAsyncData` patterns already in the codebase. This keeps `index.vue` clean and makes the fetching logic independently testable.

### D4 — TypeScript interfaces added to `types/api.ts`

`LatestDraw` and `DrawPremio` interfaces typed from the real API response. This ensures type safety when rendering and is consistent with the existing `types/api.ts` pattern.

## Risks / Trade-offs

- **[Risk] Third-party API unavailability** → Mitigation: render a user-friendly error state with a retry prompt; the page degrades gracefully rather than crashing.
- **[Risk] API shape changes** → Mitigation: the response shape has been stable; TypeScript interfaces will surface mismatches during development. Mark fields as optional where the API occasionally omits them.
- **[Risk] CORS issues in production** → Mitigation: the proxy already sets permissive CORS headers; tested successfully in browser fetch. If it fails, the error state is shown.
