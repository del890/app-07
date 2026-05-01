<script setup lang="ts">
import type { ScenarioPathPrediction } from '~/types/api'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'

const { status, events, result, error, predictScenarioPath, reset } = useSsePrediction()

const horizon = ref(3)
const prediction = computed(() => result.value as ScenarioPathPrediction | null)
const isStreaming = computed(() => status.value === 'streaming')
const isDone = computed(() => status.value === 'done')
const isCalibrated = computed(() => prediction.value?.calibrated === true)

function start() {
  reset()
  predictScenarioPath({ horizon: horizon.value })
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <Button variant="ghost" as-child class="-ml-3 mb-1">
        <NuxtLink to="/play">← Jogar</NuxtLink>
      </Button>
      <h1 class="text-2xl font-bold">Caminho de Cenário</h1>
    </div>

    <div class="flex items-center gap-4">
      <label class="flex items-center gap-2 text-sm">
        Horizonte (sorteios à frente)
        <Input
          v-model.number="horizon"
          type="number"
          min="1"
          max="10"
          class="w-20"
        />
      </label>
      <Button :disabled="isStreaming" @click="start">
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
        {{ isStreaming ? 'Gerando…' : 'Gerar Cenário' }}
      </Button>
    </div>

    <!-- Streaming tool events -->
    <div class="max-w-xl">
      <ToolProgressTimeline :events="events" />
    </div>

    <!-- Uncalibrated banner -->
    <div v-if="isDone && !isCalibrated" class="bg-warning/10 border border-warning/30 rounded-lg p-5 max-w-xl">
      <h2 class="font-semibold text-warning-foreground mb-1">Calibração Necessária</h2>
      <p class="text-sm text-warning-foreground/80">
        O motor de previsão não está calibrado. Caminhos de cenário não podem ser exibidos.
      </p>
      <Button variant="ghost" as-child class="mt-2 -ml-3">
        <NuxtLink to="/research">Explorar dados de pesquisa →</NuxtLink>
      </Button>
    </div>

    <!-- Path steps — monotonically non-increasing confidence (13.4) -->
    <div v-if="isDone && isCalibrated && prediction" class="space-y-4 max-w-xl">
      <PredictionCard
        v-for="step in prediction.path"
        :key="step.step"
        :label="`Draw +${step.step}`"
        :numbers="step.numbers"
        :confidence="step.confidence"
        :explanation="step.explanation"
        :provenance="prediction.provenance"
      />

      <div class="text-xs text-muted-foreground">
        Conjunto de dados: {{ prediction.provenance.dataset_hash.slice(0, 12) }}
        · {{ prediction.provenance.computed_at }}
      </div>
    </div>

    <div v-if="status === 'error'" class="text-destructive text-sm">{{ error }}</div>

    <!-- History link shown after a prediction is saved -->
    <div v-if="isDone && isCalibrated && prediction">
      <Button variant="ghost" as-child class="-ml-3">
        <NuxtLink to="/play/history">Ver previsões salvas →</NuxtLink>
      </Button>
    </div>
  </div>
</template>
