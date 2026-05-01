// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
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
      apiBase: process.env.NUXT_PUBLIC_API_BASE ?? 'http://localhost:8000',
    },
  },
})
