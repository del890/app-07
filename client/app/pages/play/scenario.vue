<script setup lang="ts">
import type { ScenarioPathPrediction } from '~/types/api'

const { status, result, error, predictScenarioPath, reset } = useSsePrediction()

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
        class="px-6 py-2.5 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50"
        :disabled="isStreaming"
        @click="start"
      >
        {{ isStreaming ? 'Generating…' : 'Generate Scenario' }}
      </button>
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
      <div
        v-for="step in prediction.path"
        :key="step.step"
        class="bg-white rounded-lg border border-gray-200 p-4"
      >
        <div class="flex items-center gap-3 mb-3">
          <span class="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">
            Draw +{{ step.step }}
          </span>
          <ConfidenceBadge :confidence="step.confidence" />
        </div>
        <div class="flex flex-wrap gap-1.5 mb-3">
          <span
            v-for="n in step.numbers"
            :key="n"
            class="w-8 h-8 flex items-center justify-center rounded-full bg-indigo-100 text-indigo-800 font-bold text-xs"
          >
            {{ n }}
          </span>
        </div>
        <p class="text-xs text-gray-500">{{ step.explanation }}</p>
      </div>

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
