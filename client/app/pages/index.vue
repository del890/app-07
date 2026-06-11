<script setup lang="ts">
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Card, CardContent, CardHeader } from '~/components/ui/card'
import type { DrawPremio } from '~/types/api'

const { draws, pending, error, retry } = useLatestDraws()

function topPrize(premiacoes: DrawPremio[]): DrawPremio | undefined {
  return premiacoes.find(p => p.faixa === 1)
}

function formatCurrency(value: number): string {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}
</script>

<template>
  <div class="max-w-2xl sm:max-w-3xl mx-auto py-6 sm:py-10 space-y-8 px-0">
    <!-- Header -->
    <div class="text-center space-y-2">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/25 text-primary text-xs font-semibold tracking-wide uppercase">
        Lotofácil · Últimos Sorteios
      </div>
      <h1 class="text-3xl font-bold bg-gradient-to-r from-primary via-primary/80 to-[hsl(165,100%,39%)] bg-clip-text text-transparent">
        Resultados Recentes
      </h1>
    </div>

    <!-- Loading skeletons -->
    <div v-if="pending" class="space-y-4">
      <Card v-for="n in 3" :key="n" class="animate-pulse">
        <CardHeader class="pb-3">
          <div class="h-5 w-32 rounded bg-muted" />
        </CardHeader>
        <CardContent class="space-y-3">
          <div class="flex flex-wrap gap-2">
            <div v-for="i in 15" :key="i" class="w-9 h-9 rounded-full bg-muted" />
          </div>
          <div class="h-4 w-48 rounded bg-muted" />
        </CardContent>
      </Card>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="text-center space-y-4 py-8">
      <p class="text-destructive font-medium">Não foi possível carregar os sorteios.</p>
      <p class="text-muted-foreground text-sm">{{ error.message }}</p>
      <Button variant="outline" @click="retry">Tentar novamente</Button>
    </div>

    <!-- Draw cards -->
    <div v-else class="space-y-4">
      <Card v-for="draw in draws" :key="draw.concurso">
        <CardHeader class="pb-3">
          <div class="flex items-center justify-between flex-wrap gap-2">
            <div class="flex items-center gap-2">
              <span class="font-semibold text-base">Concurso {{ draw.concurso }}</span>
              <span class="text-muted-foreground text-sm">{{ draw.data }}</span>
            </div>
            <Badge v-if="draw.acumulou" variant="destructive" class="text-xs">
              Acumulou
            </Badge>
          </div>
        </CardHeader>
        <CardContent class="space-y-4">
          <!-- Number badges -->
          <div class="flex flex-wrap gap-2">
            <span
              v-for="num in draw.dezenas"
              :key="num"
              class="w-10 h-10 flex items-center justify-center rounded-full font-bold text-sm bg-primary text-primary-foreground"
            >
              {{ parseInt(num) }}
            </span>
          </div>
          <!-- Top prize info -->
          <div v-if="topPrize(draw.premiacoes)" class="text-sm text-muted-foreground flex items-center gap-2">
            <span>15 acertos:</span>
            <span class="font-medium text-foreground">
              {{ topPrize(draw.premiacoes)!.ganhadores }}
              {{ topPrize(draw.premiacoes)!.ganhadores === 1 ? 'ganhador' : 'ganhadores' }}
            </span>
            <span v-if="topPrize(draw.premiacoes)!.ganhadores > 0" class="text-primary font-semibold">
              {{ formatCurrency(topPrize(draw.premiacoes)!.valorPremio) }}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Navigation -->
    <div class="flex justify-center gap-4 pt-2">
      <Button as-child size="lg">
        <NuxtLink to="/research">Modo Pesquisa</NuxtLink>
      </Button>
      <Button as-child variant="secondary" size="lg">
        <NuxtLink to="/play">Modo Jogar</NuxtLink>
      </Button>
    </div>
  </div>
</template>
