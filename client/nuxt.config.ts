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
      apiBase: process.env.NUXT_PUBLIC_API_BASE ?? 'http://localhost:5000',
    },
  },
})
