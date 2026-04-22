---
name: client-stack
description: Enforces the client tech stack for this project. Use whenever building, scaffolding, or modifying client-side / frontend code, or when the user asks to create UI, pages, components, or a web app. The client MUST be built with Nuxt.js and TypeScript.
---

# Client Stack

The client application for this project **must** be built with:

- **Framework**: [Nuxt.js](https://nuxt.com) (Nuxt 3+, latest stable)
- **Language**: TypeScript (strict mode)

Apply this skill any time you are creating, scaffolding, or modifying client-side code. Do not substitute another framework (no plain Vue CLI, Next.js, SvelteKit, Remix, CRA, Vite-only SPA, etc.) unless the user explicitly overrides this rule in their request.

---

## Required setup

When scaffolding a new client, use the official Nuxt starter and enable TypeScript from the start:

```bash
npx nuxi@latest init client
cd client
npm install
```

Then ensure TypeScript is treated as a first-class citizen:

1. **`nuxt.config.ts`** — always use the `.ts` extension, and enable strict typechecking:

   ```ts
   export default defineNuxtConfig({
     typescript: {
       strict: true,
       typeCheck: true,
     },
   })
   ```

2. **`tsconfig.json`** — extend Nuxt's generated config:

   ```json
   {
     "extends": "./.nuxt/tsconfig.json"
   }
   ```

3. **File extensions** — use `.ts` for scripts/composables/plugins/server routes and `<script setup lang="ts">` in every Vue single-file component. No `.js` files in the client.

---

## Conventions

- **Directory layout**: follow Nuxt's convention-over-configuration structure — `pages/`, `components/`, `composables/`, `layouts/`, `server/`, `middleware/`, `plugins/`, `assets/`, `public/`.
- **Routing**: file-based routing via `pages/`. Do not hand-roll a router.
- **Data fetching**: prefer `useFetch` / `useAsyncData` over raw `fetch` in components.
- **State**: use `useState` for simple shared state; add Pinia only if genuinely needed.
- **Server code**: put API routes in `server/api/` (Nitro). Don't spin up a separate Express/Fastify server for the client's own API unless the user asks.
- **Types**: define shared types in `types/` or co-located `*.types.ts` files. Avoid `any`; prefer `unknown` + narrowing.
- **Styling**: pick one approach and stick to it (Tailwind, UnoCSS, or scoped SFC styles). Don't mix.

---

## Guardrails

- If the user asks to build client/frontend/UI code and no client exists yet, scaffold it with Nuxt + TypeScript as described above.
- If an existing client is present, verify it is Nuxt + TypeScript before extending it. If it is not, stop and flag the mismatch to the user instead of silently adding to a non-conforming stack.
- Do not introduce JavaScript (`.js`) source files into the client — TypeScript only.
- Do not add a different frontend framework alongside Nuxt "just for this one feature." Build within Nuxt.
- If the user explicitly overrides this rule for a specific task, follow their instruction but call out that you are deviating from the project's client stack.
