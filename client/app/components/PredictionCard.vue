<script setup lang="ts">
import type { PredictionProvenance } from '~/types/api'
import { normalizePredictionExplanation } from '~/composables/usePredictionExplanation'

const props = defineProps<{
  numbers: number[]
  confidence: number
  explanation: unknown
  provenance: PredictionProvenance
  label?: string
}>()

const barColor = computed(() => {
  if (props.confidence >= 0.7) return 'bg-green-500'
  if (props.confidence >= 0.4) return 'bg-yellow-400'
  return 'bg-red-500'
})

const barWidth = computed(() => `${Math.round(props.confidence * 100)}%`)

const explanationView = computed(() => normalizePredictionExplanation(props.explanation))
</script>

<template>
  <div class="bg-white rounded-lg border border-gray-200 p-6">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-4">
      <h2 v-if="label" class="text-sm font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">
        {{ label }}
      </h2>
      <h2 v-else class="font-semibold text-lg">Números Sugeridos</h2>
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
        <span>Confiança</span>
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
    <div class="space-y-4 mb-4">
      <p class="max-w-prose text-sm sm:text-base leading-relaxed text-gray-700">
        {{ explanationView.summary }}
      </p>

      <section
        v-for="section in explanationView.highlightSections"
        :key="section.key"
        class="rounded-lg border border-gray-200 bg-gray-50/80 p-3"
      >
        <h3 class="text-xs font-semibold uppercase tracking-wide text-gray-600 mb-2">
          {{ section.title }}
        </h3>
        <ul v-if="section.items.length" class="space-y-1.5 text-sm text-gray-700">
          <li v-for="item in section.items" :key="item">
            • {{ item }}
          </li>
        </ul>
        <p v-if="section.note" class="mt-2 text-sm text-gray-600 italic">
          {{ section.note }}
        </p>
      </section>

      <section v-if="explanationView.topProbabilities.length" class="rounded-lg border border-gray-200 p-3">
        <h3 class="text-xs font-semibold uppercase tracking-wide text-gray-600 mb-2">Top probabilidades</h3>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="entry in explanationView.topProbabilities"
            :key="entry.number"
            class="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 text-indigo-700 px-2.5 py-1 text-xs font-semibold"
          >
            <span>#{{ entry.number }}</span>
            <span>{{ Math.round(entry.probability * 100) }}%</span>
          </span>
        </div>
      </section>

      <section v-if="explanationView.provenance.length" class="rounded-lg border border-emerald-200 bg-emerald-50/70 p-3">
        <h3 class="text-xs font-semibold uppercase tracking-wide text-emerald-800 mb-1">Proveniencia da analise</h3>
        <ul class="space-y-1 text-xs sm:text-sm text-emerald-900">
          <li v-for="line in explanationView.provenance" :key="line">{{ line }}</li>
        </ul>
      </section>

      <section v-if="explanationView.fallbackText" class="rounded-lg border border-amber-200 bg-amber-50 p-3">
        <h3 class="text-xs font-semibold uppercase tracking-wide text-amber-700 mb-1">Detalhes adicionais</h3>
        <p class="text-xs sm:text-sm leading-relaxed text-amber-900 break-words">
          {{ explanationView.fallbackText }}
        </p>
      </section>
    </div>

    <!-- Provenance footer (only for top-level cards, not labelled step cards) -->
    <div v-if="!label" class="text-xs text-gray-400 border-t pt-3">
      Conjunto de dados: {{ provenance.dataset_hash.slice(0, 12) }}
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
