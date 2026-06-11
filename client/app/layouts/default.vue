<script setup lang="ts">
import { useActiveGame } from '~/composables/useActiveGame'

const route = useRoute()
const router = useRouter()
const { activeGame, setActiveGame } = useActiveGame()

const mode = computed<'play' | 'home'>(() => {
  if (route.path.startsWith('/play')) return 'play'
  return 'home'
})

function switchGame(game: 'lotofacil' | 'megasena') {
  setActiveGame(game)
  router.push('/')
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-background text-foreground">
    <!-- Header -->
    <header class="sticky top-0 z-50 bg-background border-b border-border">
      <div class="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <NuxtLink
          to="/"
          class="text-sm font-medium tracking-widest uppercase hover:opacity-60 transition-opacity"
          style="font-family: var(--mono);"
        >
          Loterias <span class="opacity-40 normal-case tracking-normal text-xs font-normal">research</span>
        </NuxtLink>

        <!-- Desktop nav — hidden on mobile -->
        <nav class="hidden sm:flex items-center gap-1">
          <!-- Lotofácil game tab -->
          <button
            type="button"
            class="px-4 py-1.5 rounded-full border text-[11px] font-medium uppercase tracking-wider transition-all"
            :class="mode === 'home' && activeGame === 'lotofacil'
              ? 'bg-foreground text-background border-foreground'
              : 'bg-transparent text-foreground border-border hover:border-foreground/40'"
            style="font-family: var(--mono);"
            @click="switchGame('lotofacil')"
          >
            Lotofácil
          </button>
          <!-- Mega Sena game tab -->
          <button
            type="button"
            class="px-4 py-1.5 rounded-full border text-[11px] font-medium uppercase tracking-wider transition-all"
            :class="mode === 'home' && activeGame === 'megasena'
              ? 'bg-foreground text-background border-foreground'
              : 'bg-transparent text-foreground border-border hover:border-foreground/40'"
            style="font-family: var(--mono);"
            @click="switchGame('megasena')"
          >
            Mega Sena
          </button>
          <!-- Jogar route link -->
          <NuxtLink
            to="/play"
            class="px-4 py-1.5 rounded-full border text-[11px] font-medium uppercase tracking-wider transition-all"
            :class="mode === 'play'
              ? 'bg-foreground text-background border-foreground'
              : 'bg-transparent text-foreground border-border hover:border-foreground/40'"
            style="font-family: var(--mono);"
          >
            Jogar
          </NuxtLink>
        </nav>
      </div>
    </header>

    <!-- Main content — extra bottom padding on mobile to clear tab bar -->
    <main class="flex-1 max-w-6xl mx-auto w-full px-3 sm:px-4 py-6 pb-20 sm:pb-6">
      <slot />
    </main>

    <!-- Footer -->
    <footer
      class="py-3 text-center border-t border-border text-muted-foreground text-[10px] tracking-wider uppercase"
      style="font-family: var(--mono);"
    >
      Ferramenta de Pesquisa Loterias — não é afiliada à Caixa Econômica Federal.
    </footer>

    <!-- Mobile bottom tab bar — visible only on small screens -->
    <nav
      class="sm:hidden fixed bottom-0 inset-x-0 z-50 bg-background border-t border-border flex"
      style="padding-bottom: env(safe-area-inset-bottom, 0px);"
    >
      <!-- Lotofácil tab -->
      <button
        type="button"
        class="flex-1 flex flex-col items-center justify-center gap-1 py-3 min-h-[56px] transition-colors border-t-2 text-[9px] uppercase tracking-wider font-medium"
        :class="mode === 'home' && activeGame === 'lotofacil' ? 'text-foreground border-foreground' : 'text-muted-foreground border-transparent'"
        style="font-family: var(--mono);"
        @click="switchGame('lotofacil')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 8v4l3 3" />
        </svg>
        Lotofácil
      </button>
      <!-- Mega Sena tab -->
      <button
        type="button"
        class="flex-1 flex flex-col items-center justify-center gap-1 py-3 min-h-[56px] transition-colors border-t-2 text-[9px] uppercase tracking-wider font-medium"
        :class="mode === 'home' && activeGame === 'megasena' ? 'text-foreground border-foreground' : 'text-muted-foreground border-transparent'"
        style="font-family: var(--mono);"
        @click="switchGame('megasena')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5">
          <rect x="2" y="7" width="20" height="14" rx="2" />
          <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
          <line x1="12" y1="12" x2="12" y2="16" />
          <line x1="10" y1="14" x2="14" y2="14" />
        </svg>
        Mega Sena
      </button>
      <!-- Jogar tab -->
      <NuxtLink
        to="/play"
        class="flex-1 flex flex-col items-center justify-center gap-1 py-3 min-h-[56px] transition-colors border-t-2 text-[9px] uppercase tracking-wider font-medium"
        :class="mode === 'play' ? 'text-foreground border-foreground' : 'text-muted-foreground border-transparent'"
        style="font-family: var(--mono);"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5">
          <rect x="2" y="3" width="20" height="14" rx="2" />
          <path d="M8 21h8M12 17v4" />
        </svg>
        Jogar
      </NuxtLink>
    </nav>
  </div>
</template>


