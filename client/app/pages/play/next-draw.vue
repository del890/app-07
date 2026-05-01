<script setup lang="ts">
import type { NextDrawPrediction } from '~/types/api'
import { Button } from '~/components/ui/button'

const { status, events, result, error, predictNextDraw, reset } = useSsePrediction()

const prediction = computed(() => result.value as NextDrawPrediction | null)
const isStreaming = computed(() => status.value === 'streaming')
const isDone = computed(() => status.value === 'done')

// Guard: never render suggestion if calibrated is false (13.5)
const isCalibrated = computed(() => prediction.value?.calibrated === true)

function start() {
  reset()
  predictNextDraw()
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <Button variant="ghost" as-child class="-ml-3 mb-1">
        <NuxtLink to="/play">← Jogar</NuxtLink>
      </Button>
      <h1 class="text-2xl font-bold">Sugerir Próximo Sorteio</h1>
    </div>

    <Button size="lg" :disabled="isStreaming" @click="start">
      <svg
        v-if="isStreaming"
        class="animate-spin h-4 w-4 mr-2"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      {{ isStreaming ? 'Analisando…' : 'Gerar Sugestão' }}
    </Button>

    <!-- Streaming tool events -->
    <div class="max-w-xl">
      <ToolProgressTimeline :events="events" />
    </div>

    <!-- Uncalibrated banner (13.5) -->
    <div
      v-if="isDone && !isCalibrated"
      class="bg-warning/10 border border-warning/30 rounded-lg p-5 max-w-xl"
    >
      <h2 class="font-semibold text-warning-foreground mb-1">Calibração Necessária</h2>
      <p class="text-sm text-warning-foreground/80">
        O motor de previsão ainda não foi calibrado ou a calibração está desatualizada.
        Sugestões não podem ser exibidas neste estado.
      </p>
      <Button variant="ghost" as-child class="mt-2 -ml-3">
        <NuxtLink to="/research">Explorar dados de pesquisa →</NuxtLink>
      </Button>
    </div>

    <!-- Prediction result -->
    <div v-if="isDone && isCalibrated && prediction" class="max-w-xl">
      <PredictionCard
        :numbers="prediction.numbers"
        :confidence="prediction.confidence"
        :explanation="prediction.explanation"
        :provenance="prediction.provenance"
      />
    </div>

    <!-- Error -->
    <div v-if="status === 'error'" class="text-destructive text-sm">{{ error }}</div>

    <!-- History link shown after a prediction is saved -->
    <div v-if="isDone && isCalibrated && prediction">
      <Button variant="ghost" as-child class="-ml-3">
        <NuxtLink to="/play/history">Ver previsões salvas →</NuxtLink>
      </Button>
    </div>
  </div>
</template>
