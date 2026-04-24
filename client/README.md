# client

Nuxt 4 SPA front-end for the Lotofácil Research Tool.

- Framework: Nuxt 4 (`ssr: false`, SPA mode)
- Language: TypeScript strict
- Styling: Tailwind CSS
- Charts: Chart.js + vue-chartjs
- Tests: Vitest

## Setup

```bash
cd client
npm install
cp ../.env.example .env.local   # set NUXT_PUBLIC_API_BASE if needed
```

## Development

```bash
npm run dev      # starts on http://localhost:3000
```

Set `NUXT_PUBLIC_API_BASE=http://localhost:8000` (or in `.env.local`) to point at the service.

## Test

```bash
npm test          # Vitest unit tests
npm run copy-lint # check for banned marketing words in copy
```

## Build

```bash
npm run build      # production build → .output/
npm run generate   # static export → .output/public/
```

Static output can be served by any HTTP server (nginx, Caddy, etc.).

## Deployment

The client is a pure SPA (static files). Serve `.output/public/` with any static file host
or behind the same nginx that reverse-proxies to the service.

### Environment variables (Nuxt runtime config)

| Variable | Default | Description |
|---|---|---|
| `NUXT_PUBLIC_API_BASE` | `http://localhost:8000` | Backend service base URL |

### nginx example

```nginx
server {
    listen 80;
    root /var/www/lotofacil/public;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /v1/ {
        proxy_pass http://localhost:8000;
    }
}
```

## Routes

| Path | Mode | Description |
|---|---|---|
| `/` | — | Landing page |
| `/research` | Research | Statistical analysis index |
| `/research/frequency` | Research | Per-number frequency bar chart |
| `/research/gaps` | Research | Hot/cold gap table |
| `/research/cooccurrence` | Research | Co-occurrence explorer |
| `/research/structural` | Research | Sum/even/quintile histograms |
| `/research/order` | Research | Draw order label |
| `/research/pi-alignment` | Research | PI-alignment rule score |
| `/research/correlations` | Research | External signal correlation |
| `/play/next-draw` | Play | Streaming next-draw suggestion |
| `/play/scenario` | Play | Scenario path viewer |

# pnpm
pnpm dev

# yarn
yarn dev

# bun
bun run dev
```

## Production

Build the application for production:

```bash
# npm
npm run build

# pnpm
pnpm build

# yarn
yarn build

# bun
bun run build
```

Locally preview production build:

```bash
# npm
npm run preview

# pnpm
pnpm preview

# yarn
yarn preview

# bun
bun run preview
```

Check out the [deployment documentation](https://nuxt.com/docs/getting-started/deployment) for more information.
