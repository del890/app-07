<script setup lang="ts">
import type { PredictionProvenance } from '~/types/api'

const props = defineProps<{
  numbers: number[]
  confidence: number
  explanation: string
  provenance: PredictionProvenance
  label?: string
}>()

const barColor = computed(() => {
  if (props.confidence >= 0.7) return 'bg-green-500'
  if (props.confidence >= 0.4) return 'bg-yellow-400'
  return 'bg-red-500'
})

const barWidth = computed(() => `${Math.round(props.confidence * 100)}%`)
</script>

<template>
  <div class="bg-white rounded-lg border border-gray-200 p-6">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-4">
      <h2 v-if="label" class="text-sm font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">
        {{ label }}
      </h2>
      <h2 v-else class="font-semibold text-lg">Suggested Numbers</h2>
      <ConfidenceBadge :confidence="confidence" />
    </div>

    <!-- Staggered number bubbles -->
    <TransitionGroup
      name="numbers"
      appear
      tag="div"
      class="flex flex-wrap gap-2 mb-5"
    >
      <span
        v-for="(n, i) in numbers"
        :key="n"
        class="w-10 h-10 flex items-center justify-center rounded-full font-bold text-sm"
        :class="label ? 'bg-indigo-100 text-indigo-800' : 'bg-purple-100 text-purple-800'"
        :style="{ transitionDelay: `${i * 30}ms` }"
      >
        {{ n }}
      </span>
    </TransitionGroup>

    <!-- Confidence meter -->
    <div class="mb-4">
      <div class="flex items-center justify-between text-xs text-gray-500 mb-1">
        <span>Confidence</span>
        <span>{{ Math.round(confidence * 100) }}%</span>
      </div>
      <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-700"
          :class="barColor"
          :style="{ width: barWidth }"
        />
      </div>
    </div>

    <!-- Explanation -->
    <p class="max-w-prose text-base leading-relaxed text-gray-600 mb-4">
      {{ explanation }}
    </p>

    <!-- Provenance footer (only for top-level cards, not labelled step cards) -->
    <div v-if="!label" class="text-xs text-gray-400 border-t pt-3">
      Dataset: {{ provenance.dataset_hash.slice(0, 12) }}
      · {{ provenance.computed_at }}
    </div>
  </div>
</template>

<style scoped>
.numbers-enter-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.numbers-enter-from {
  opacity: 0;
  transform: scale(0.8);
}
</style>
