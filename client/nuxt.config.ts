// https://nuxt.com/docs/api/configuration/nuxt-config

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  nitro: {
    // ensure publicDir is not changed away from '.output/public'
    publicDir: '.output/public'
  },

  ssr: false,

  // Sorte UI design-system styles (tokens, reset, base) first, then app-level
  // layout helpers. Fonts (Poppins + Inter) are pulled in by tokens.css.
  css: ['~/sorte-ui/styles/index.css', '~/assets/css/main.css'],

  modules: ['@nuxt/eslint'],

  typescript: {
    strict: true,
    typeCheck: false, // run separately to avoid blocking dev server
  },

  runtimeConfig: {
    public: {
      // Production (EB): leave empty so API calls hit relative `/v1/...` on the
      // UI origin, where nginx proxies them to the backend service (see
      // client/default.conf.template). Local dev: set NUXT_PUBLIC_API_BASE in
      // client/.env to point directly at the service (no nginx proxy locally).
      apiBase: process.env.NUXT_PUBLIC_API_BASE ?? '',
    },
  },
})
