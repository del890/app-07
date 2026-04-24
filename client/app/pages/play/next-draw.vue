<script setup lang="ts">
import type { NextDrawPrediction } from '~/types/api'

const { status, events, result, error, predictNextDraw, reset } = useSsePrediction()

const prediction = computed(() => result.value as NextDrawPrediction | null)
const isStreaming = computed(() => status.value === 'streaming')
const isDone = computed(() => status.value === 'done')

// Guard: never render suggestion if calibrated is false (13.5)
const isCalibrated = computed(() => prediction.value?.calibrated === true)

const toolEvents = computed(() =>
  events.value.filter((e) => e.type === 'tool_start' || e.type === 'tool_result'),
)

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
      class="px-6 py-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 transition-colors disabled:opacity-50"
      :disabled="isStreaming"
      @click="start"
    >
      {{ isStreaming ? 'Analysing…' : 'Generate Suggestion' }}
    </button>

    <!-- Streaming tool events -->
    <div v-if="toolEvents.length" class="mt-6 space-y-2 max-w-xl">
      <div
        v-for="(ev, i) in toolEvents"
        :key="i"
        class="text-xs font-mono bg-gray-50 border border-gray-200 rounded px-3 py-2"
      >
        <span v-if="ev.type === 'tool_start'" class="text-blue-600">▶ {{ ev.tool_name }}</span>
        <span v-else-if="ev.type === 'tool_result'" class="text-green-600">✓ {{ ev.tool_name }}</span>
      </div>
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
    <div v-if="isDone && isCalibrated && prediction" class="mt-6 bg-white rounded-lg border border-gray-200 p-6 max-w-xl">
      <div class="flex items-center gap-3 mb-4">
        <h2 class="font-semibold text-lg">Suggested Numbers</h2>
        <ConfidenceBadge :confidence="prediction.confidence" />
      </div>

      <!-- 15-number grid -->
      <div class="flex flex-wrap gap-2 mb-4">
        <span
          v-for="n in prediction.numbers"
          :key="n"
          class="w-10 h-10 flex items-center justify-center rounded-full bg-purple-100 text-purple-800 font-bold text-sm"
        >
          {{ n }}
        </span>
      </div>

      <p class="text-sm text-gray-600 mb-4">{{ prediction.explanation }}</p>

      <div class="text-xs text-gray-400 border-t pt-3">
        Dataset: {{ prediction.provenance.dataset_hash.slice(0, 12) }}
        · {{ prediction.provenance.computed_at }}
      </div>
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
