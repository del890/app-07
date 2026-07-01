// Registers the vendored Sorte UI design system globally so every
// component (SButton, SCard, SLotteryBall, …) is available in templates
// without a per-file import. See app/sorte-ui/index.js.
import { SorteUI } from '~/sorte-ui'

export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.use(SorteUI)
})
