<script setup lang="ts">
import type { ScenarioPathPrediction } from '~/types/api'

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
  <div>
    <NuxtLink to="/play" class="text-sm text-blue-600 hover:underline mb-4 block">← Play</NuxtLink>
    <h1 class="text-2xl font-bold mb-6">Scenario Path</h1>

    <div class="flex items-center gap-4 mb-6">
      <label class="flex items-center gap-2 text-sm">
        Horizon (draws ahead)
        <input
          v-model.number="horizon"
          type="number"
          min="1"
          max="10"
          class="border rounded px-2 py-1.5 w-20 focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
      </label>
      <button
        class="inline-flex items-center gap-2 px-6 py-2.5 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50"
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
        {{ isStreaming ? 'Generating…' : 'Generate Scenario' }}
      </button>
    </div>

    <!-- Streaming tool events -->
    <div class="max-w-xl">
      <ToolProgressTimeline :events="events" />
    </div>

    <!-- Uncalibrated banner -->
    <div v-if="isDone && !isCalibrated" class="bg-amber-50 border border-amber-300 rounded-lg p-5 max-w-xl">
      <h2 class="font-semibold text-amber-800 mb-1">Calibration Required</h2>
      <p class="text-sm text-amber-700">
        The prediction engine is not calibrated. Scenario paths cannot be shown.
      </p>
      <NuxtLink to="/research" class="mt-3 inline-block text-sm text-blue-600 hover:underline">
        Explore research data instead →
      </NuxtLink>
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

      <div class="text-xs text-gray-400">
        Dataset: {{ prediction.provenance.dataset_hash.slice(0, 12) }}
        · {{ prediction.provenance.computed_at }}
      </div>
    </div>

    <div v-if="status === 'error'" class="mt-4 text-red-600 text-sm">{{ error }}</div>

    <!-- History link shown after a prediction is saved -->
    <div v-if="isDone && isCalibrated && prediction" class="mt-4">
      <NuxtLink to="/play/history" class="text-sm text-gray-500 hover:text-gray-700 hover:underline">
        View saved predictions →
      </NuxtLink>
    </div>
  </div>
</template>
