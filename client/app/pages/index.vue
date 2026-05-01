<script setup lang="ts">
import { Button } from '~/components/ui/button'
</script>

<template>
  <div class="text-center py-16 space-y-8">
    <div class="space-y-4">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/25 text-primary text-xs font-semibold tracking-wide uppercase">
        Lotofácil · Análise Estatística
      </div>
      <h1 class="text-4xl font-bold bg-gradient-to-r from-primary via-primary/80 to-[hsl(165,100%,39%)] bg-clip-text text-transparent">
        Ferramenta de Pesquisa
      </h1>
      <p class="text-muted-foreground max-w-xl mx-auto">
        Explore estatísticas históricas de sorteios e pesquise padrões. Análise estatística apenas —
        nenhuma previsão é certa.
      </p>
    </div>
    <div class="flex justify-center gap-4">
      <Button as-child size="lg">
        <NuxtLink to="/research">Modo Pesquisa</NuxtLink>
      </Button>
      <Button as-child variant="secondary" size="lg">
        <NuxtLink to="/play">Modo Jogar</NuxtLink>
      </Button>
    </div>
  </div>
</template>
