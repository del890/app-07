<script setup lang="ts">
import type { NextDrawPrediction } from '~/types/api'

const { status, events, result, error, predictNextDraw, reset } = useSsePrediction()

const prediction = computed(() => result.value as NextDrawPrediction | null)

// Guard: never show suggestion if calibrated is false
const canShow = computed(() => prediction.value?.calibrated === true)

async function request() {
  await predictNextDraw()
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-2">Modo Jogar</h1>
    <p class="text-sm text-gray-500 mb-1">Apenas para fins de pesquisa e entretenimento.</p>
    <p class="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-1.5 mb-6 inline-block">
      Padrões estatísticos não garantem resultados futuros. Jogue com responsabilidade.
    </p>

    <div class="flex gap-4 mb-6">
      <NuxtLink
        to="/play/next-draw"
        class="px-5 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
      >
        Sugerir Próximo Sorteio
      </NuxtLink>
      <NuxtLink
        to="/play/scenario"
        class="px-5 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
      >
        Caminho de Cenário
      </NuxtLink>
      <NuxtLink
        to="/play/my-draw"
        class="px-5 py-3 bg-teal-600 text-white rounded-lg font-medium hover:bg-teal-700 transition-colors"
      >
        Meu Volante
      </NuxtLink>
      <NuxtLink
        to="/play/history"
        class="px-5 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
      >
        Histórico
      </NuxtLink>
    </div>

    <NuxtPage />
  </div>
</template>
