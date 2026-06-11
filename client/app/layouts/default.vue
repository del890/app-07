<script setup lang="ts">
const route = useRoute()

const mode = computed<'research' | 'play'>(() => {
  if (route.path.startsWith('/play')) return 'play'
  return 'research'
})
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
          Lotofácil <span class="opacity-40 normal-case tracking-normal text-xs font-normal">research</span>
        </NuxtLink>

        <!-- Desktop mode nav — hidden on mobile -->
        <nav class="hidden sm:flex items-center gap-1">
          <NuxtLink
            to="/research"
            class="px-4 py-1.5 rounded-full border text-[11px] font-medium uppercase tracking-wider transition-all"
            :class="mode === 'research'
              ? 'bg-foreground text-background border-foreground'
              : 'bg-transparent text-foreground border-border hover:border-foreground/40'"
            style="font-family: var(--mono);"
          >
            Pesquisa
          </NuxtLink>
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
      Ferramenta de Pesquisa Lotofácil — não é afiliada à Caixa Econômica Federal.
    </footer>

    <!-- Mobile bottom tab bar — visible only on small screens -->
    <nav
      class="sm:hidden fixed bottom-0 inset-x-0 z-50 bg-background border-t border-border flex"
      style="padding-bottom: env(safe-area-inset-bottom, 0px);"
    >
      <NuxtLink
        to="/research"
        class="flex-1 flex flex-col items-center justify-center gap-1 py-3 min-h-[56px] transition-colors border-t-2 text-[10px] uppercase tracking-wider font-medium"
        :class="mode === 'research' ? 'text-foreground border-foreground' : 'text-muted-foreground border-transparent'"
        style="font-family: var(--mono);"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <path d="M3 9h18M9 3v18" />
        </svg>
        Pesquisa
      </NuxtLink>
      <NuxtLink
        to="/play"
        class="flex-1 flex flex-col items-center justify-center gap-1 py-3 min-h-[56px] transition-colors border-t-2 text-[10px] uppercase tracking-wider font-medium"
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

