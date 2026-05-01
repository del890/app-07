<script setup lang="ts">
import { Badge } from '~/components/ui/badge'

const route = useRoute()

const mode = computed<'research' | 'play'>(() => {
  if (route.path.startsWith('/play')) return 'play'
  return 'research'
})
</script>

<template>
  <div class="min-h-screen flex flex-col bg-background text-foreground" style="background-image: radial-gradient(ellipse at 10% 0%, hsl(227 100% 59% / 0.05) 0%, transparent 50%), radial-gradient(ellipse at 90% 100%, hsl(165 100% 39% / 0.04) 0%, transparent 50%)">
    <!-- Header -->
    <header class="sticky top-0 z-50 border-b border-white/10" style="background: linear-gradient(160deg, #1A2238 0%, #1e2d4a 60%, #1d3050 100%); backdrop-filter: blur(12px);">
      <div class="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <NuxtLink to="/" class="text-xl font-bold tracking-tight text-white hover:text-blue-300 transition-colors">
          Lotofácil Research
        </NuxtLink>

        <!-- Mode indicator -->
        <nav class="flex items-center gap-2">
          <NuxtLink
            to="/research"
            class="px-4 py-1.5 rounded-full text-sm font-medium transition-all"
            :class="mode === 'research'
              ? 'bg-white/15 text-white border border-white/25 shadow-sm'
              : 'text-white/60 hover:text-white hover:bg-white/10 border border-transparent'"
          >
            Pesquisa
            <Badge v-if="mode === 'research'" class="ml-1 text-xs py-0 px-1.5 bg-blue-400/25 text-blue-200 border-0">ativo</Badge>
          </NuxtLink>
          <NuxtLink
            to="/play"
            class="px-4 py-1.5 rounded-full text-sm font-medium transition-all"
            :class="mode === 'play'
              ? 'bg-white/15 text-white border border-white/25 shadow-sm'
              : 'text-white/60 hover:text-white hover:bg-white/10 border border-transparent'"
          >
            Jogar
            <Badge v-if="mode === 'play'" class="ml-1 text-xs py-0 px-1.5 bg-blue-400/25 text-blue-200 border-0">ativo</Badge>
          </NuxtLink>
        </nav>
      </div>
    </header>

    <!-- Aviso de pesquisa / entretenimento (sempre visível) -->
    <div class="bg-warning/10 border-b border-warning/30 px-4 py-2 text-center text-xs text-warning-foreground">
      Apenas para fins de pesquisa e entretenimento. Análise estatística não prevê resultados
      futuros da loteria. Jogue com responsabilidade.
    </div>

    <!-- Main content -->
    <main class="flex-1 max-w-6xl mx-auto w-full px-4 py-6">
      <slot />
    </main>

    <!-- Rodapé -->
    <footer class="py-4 text-center text-xs text-muted-foreground border-t border-border" style="background: linear-gradient(160deg, #1A2238 0%, #1e2d4a 100%); color: rgba(255,255,255,0.5);">
      Ferramenta de Pesquisa Lotofácil — não é afiliada à Caixa Econômica Federal.
    </footer>
  </div>
</template>
