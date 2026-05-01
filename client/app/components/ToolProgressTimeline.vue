<script setup lang="ts">
import type { SseEvent } from '~/types/api'

const props = defineProps<{
  events: SseEvent[]
}>()

// ── Tool name humanisation map ────────────────────────────────────────────
const TOOL_LABELS: Record<string, string> = {
  fetch_frequency_statistics: 'Estatísticas de frequência',
  fetch_gap_analysis: 'Análise de intervalos',
  fetch_cooccurrence_statistics: 'Estatísticas de co-ocorrência',
  fetch_structural_statistics: 'Estatísticas estruturais',
  fetch_correlation_signals: 'Sinais de correlação',
  fetch_prediction_history: 'Previsões recentes',
  fetch_dataset_provenance: 'Provenênça do conjunto de dados',
  fetch_draws: 'Sorteios históricos',
  run_calibration_check: 'Verificação de calibração',
  compute_draw_profile: 'Perfil de sorteio',
}

function humanise(toolName: string): string {
  return (
    TOOL_LABELS[toolName] ??
    toolName
      .split('_')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ')
  )
}

// ── Derive step list from event pairs ────────────────────────────────────
interface Step {
  toolName: string
  label: string
  state: 'running' | 'done'
}

const steps = computed<Step[]>(() => {
  const map = new Map<string, Step>()
  const order: string[] = []

  for (const ev of props.events) {
    if (ev.type === 'tool_start') {
      if (!map.has(ev.tool_name)) order.push(ev.tool_name)
      map.set(ev.tool_name, {
        toolName: ev.tool_name,
        label: humanise(ev.tool_name),
        state: 'running',
      })
    } else if (ev.type === 'tool_result') {
      const existing = map.get(ev.tool_name)
      if (existing) {
        map.set(ev.tool_name, { ...existing, state: 'done' })
      }
    }
  }

  return order.map((name) => map.get(name)!)
})

const hasSteps = computed(() => steps.value.length > 0)
</script>

<template>
  <div v-if="hasSteps" class="mt-6 max-w-xl">
    <TransitionGroup
      name="step"
      tag="ul"
      class="space-y-2"
    >
      <li
        v-for="step in steps"
        :key="step.toolName"
        class="flex items-center gap-3 text-sm"
      >
        <!-- State indicator -->
        <span class="relative flex h-5 w-5 shrink-0 items-center justify-center">
          <!-- Running: pulsing ring -->
          <span
            v-if="step.state === 'running'"
            class="absolute inline-flex h-full w-full rounded-full bg-primary/60 opacity-75 animate-ping"
          />
          <span
            v-if="step.state === 'running'"
            class="relative inline-flex h-3 w-3 rounded-full bg-primary"
          />
          <!-- Done: checkmark -->
          <svg
            v-else
            class="h-5 w-5 text-success"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fill-rule="evenodd"
              d="M16.707 5.293a1 1 0 00-1.414 0L8 12.586 4.707 9.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l8-8a1 1 0 000-1.414z"
              clip-rule="evenodd"
            />
          </svg>
        </span>

        <!-- Label -->
        <span
          :class="step.state === 'running' ? 'text-foreground font-medium' : 'text-muted-foreground'"
        >
          {{ step.label }}
        </span>
      </li>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.step-enter-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.step-enter-from {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
