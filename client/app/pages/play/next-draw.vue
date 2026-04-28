<script setup lang="ts">
import type { NextDrawPrediction } from '~/types/api'

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
  <div>
    <NuxtLink to="/play" class="text-sm text-blue-600 hover:underline mb-4 block">← Play</NuxtLink>
    <h1 class="text-2xl font-bold mb-6">Suggest Next Draw</h1>

    <button
      class="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 transition-colors disabled:opacity-50"
      :disabled="isStreaming"
      @click="start"
    >
      <svg
        v-if="isStreaming"
        class="animate-spin h-4 w-4"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      {{ isStreaming ? 'Analysing…' : 'Generate Suggestion' }}
    </button>

    <!-- Streaming tool events -->
    <div class="mt-6 max-w-xl">
      <ToolProgressTimeline :events="events" />
    </div>

    <!-- Uncalibrated banner (13.5) -->
    <div
      v-if="isDone && !isCalibrated"
      class="mt-6 bg-amber-50 border border-amber-300 rounded-lg p-5 max-w-xl"
    >
      <h2 class="font-semibold text-amber-800 mb-1">Calibration Required</h2>
      <p class="text-sm text-amber-700">
        The prediction engine has not been calibrated yet or calibration is stale.
        Suggestions cannot be displayed in this state.
      </p>
      <NuxtLink to="/research" class="mt-3 inline-block text-sm text-blue-600 hover:underline">
        Explore research data instead →
      </NuxtLink>
    </div>

    <!-- Prediction result -->
    <div v-if="isDone && isCalibrated && prediction" class="mt-6 max-w-xl">
      <PredictionCard
        :numbers="prediction.numbers"
        :confidence="prediction.confidence"
        :explanation="prediction.explanation"
        :provenance="prediction.provenance"
      />
    </div>

    <!-- Error -->
    <div v-if="status === 'error'" class="mt-4 text-red-600 text-sm">{{ error }}</div>

    <!-- History link shown after a prediction is saved -->
    <div v-if="isDone && isCalibrated && prediction" class="mt-4">
      <NuxtLink to="/play/history" class="text-sm text-gray-500 hover:text-gray-700 hover:underline">
        View saved predictions →
      </NuxtLink>
    </div>
  </div>
</template>
