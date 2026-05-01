<script setup lang="ts">
import type { PredictionProvenance } from '~/types/api'
import { normalizePredictionExplanation } from '~/composables/usePredictionExplanation'
import { Card, CardContent, CardHeader } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'

const props = defineProps<{
  numbers: number[]
  confidence: number
  explanation: unknown
  provenance: PredictionProvenance
  label?: string
}>()

const barColor = computed(() => {
  if (props.confidence >= 0.7) return 'bg-success'
  if (props.confidence >= 0.4) return 'bg-warning'
  return 'bg-destructive'
})

const barWidth = computed(() => `${Math.round(props.confidence * 100)}%`)

const explanationView = computed(() => normalizePredictionExplanation(props.explanation))
</script>

<template>
  <Card>
    <CardHeader class="pb-3">
      <!-- Header -->
      <div class="flex items-center gap-3">
        <Badge v-if="label" variant="secondary" class="text-primary font-semibold">
          {{ label }}
        </Badge>
        <h2 v-else class="font-semibold text-lg">Números Sugeridos</h2>
        <ConfidenceBadge :confidence="confidence" />
      </div>
    </CardHeader>

    <CardContent class="space-y-4">
      <!-- Staggered number bubbles -->
      <TransitionGroup
        name="numbers"
        appear
        tag="div"
        class="flex flex-wrap gap-2"
      >
        <span
          v-for="(n, i) in numbers"
          :key="n"
          class="w-10 h-10 flex items-center justify-center rounded-full font-bold text-sm bg-accent text-accent-foreground"
          :style="{ transitionDelay: `${i * 30}ms` }"
        >
          {{ n }}
        </span>
      </TransitionGroup>

      <!-- Confidence meter -->
      <div>
        <div class="flex items-center justify-between text-xs text-muted-foreground mb-1">
          <span>Confiança</span>
          <span>{{ Math.round(confidence * 100) }}%</span>
        </div>
        <div class="h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-700"
            :class="barColor"
            :style="{ width: barWidth }"
          />
        </div>
      </div>

      <!-- Explanation -->
      <div class="space-y-3">
        <p class="max-w-prose text-sm sm:text-base leading-relaxed text-foreground">
          {{ explanationView.summary }}
        </p>

        <section
          v-for="section in explanationView.highlightSections"
          :key="section.key"
          class="rounded-lg border bg-muted/50 p-3"
        >
          <h3 class="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
            {{ section.title }}
          </h3>
          <ul v-if="section.items.length" class="space-y-1.5 text-sm">
            <li v-for="item in section.items" :key="item">
              • {{ item }}
            </li>
          </ul>
          <p v-if="section.note" class="mt-2 text-sm text-muted-foreground italic">
            {{ section.note }}
          </p>
        </section>

        <section v-if="explanationView.topProbabilities.length" class="rounded-lg border p-3">
          <h3 class="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">Top probabilidades</h3>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="entry in explanationView.topProbabilities"
              :key="entry.number"
              class="inline-flex items-center gap-1.5 rounded-full bg-accent text-accent-foreground px-2.5 py-1 text-xs font-semibold"
            >
              <span>#{{ entry.number }}</span>
              <span>{{ Math.round(entry.probability * 100) }}%</span>
            </span>
          </div>
        </section>

        <section v-if="explanationView.provenance.length" class="rounded-lg border border-success/30 bg-success/5 p-3">
          <h3 class="text-xs font-semibold uppercase tracking-wide text-success mb-1">Proveniencia da analise</h3>
          <ul class="space-y-1 text-xs sm:text-sm">
            <li v-for="line in explanationView.provenance" :key="line">{{ line }}</li>
          </ul>
        </section>

        <section v-if="explanationView.fallbackText" class="rounded-lg border border-warning/30 bg-warning/5 p-3">
          <h3 class="text-xs font-semibold uppercase tracking-wide text-warning mb-1">Detalhes adicionais</h3>
          <p class="text-xs sm:text-sm leading-relaxed break-words">
            {{ explanationView.fallbackText }}
          </p>
        </section>
      </div>

      <!-- Provenance footer (only for top-level cards, not labelled step cards) -->
      <div v-if="!label" class="text-xs text-muted-foreground border-t pt-3">
        Conjunto de dados: {{ provenance.dataset_hash.slice(0, 12) }}
        · {{ provenance.computed_at }}
      </div>
    </CardContent>
  </Card>
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
