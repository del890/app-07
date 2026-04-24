import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt({
  rules: {
    // Enforce TypeScript-only source files in client/
    'no-restricted-syntax': [
      'error',
      {
        selector: "ImportDeclaration[source.value=/\\.js$/]",
        message: 'Use .ts imports only — no .js source files in the client.',
      },
    ],
  },
})
