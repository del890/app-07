<script setup lang="ts">
import type { NextDrawPrediction } from '~/types/api'
import { Button } from '~/components/ui/button'

const { status, events, result, error, predictNextDraw, reset } = useSsePrediction()

const prediction = computed(() => result.value as NextDrawPrediction | null)

// Guard: never show suggestion if calibrated is false
const canShow = computed(() => prediction.value?.calibrated === true)

async function request() {
  await predictNextDraw()
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold mb-1">Minha Área de Jogos</h1>
    </div>

    <div class="flex flex-wrap gap-3">
      <Button as-child>
        <NuxtLink to="/play/next-draw">Sugerir Próximo Sorteio</NuxtLink>
      </Button>
      <Button as-child>
        <NuxtLink to="/play/scenario">Caminho de Cenário</NuxtLink>
      </Button>
      <Button as-child>
        <NuxtLink to="/play/my-draw">Meu Volante</NuxtLink>
      </Button>
      <Button as-child>
        <NuxtLink to="/play/dream">Oráculo dos Sonhos</NuxtLink>
      </Button>
      <Button variant="secondary" as-child>
        <NuxtLink to="/play/history">Histórico</NuxtLink>
      </Button>
    </div>

    <NuxtPage />
  </div>
</template>
