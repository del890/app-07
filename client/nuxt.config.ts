// https://nuxt.com/docs/api/configuration/nuxt-config

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  app: {
    head: {
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500&display=swap',
        },
      ],
    },
  },
  nitro: {
    // ensure publicDir is not changed away from '.output/public'
    publicDir: '.output/public'
  },

  ssr: false,

  css: ['~/assets/css/main.css'],

  modules: ['@nuxtjs/tailwindcss', '@nuxt/eslint'],

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
