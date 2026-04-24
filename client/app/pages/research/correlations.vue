<script setup lang="ts">
import type { CorrelationResult } from '~/types/api'

const { post } = useApi()

const signalName = ref('')
const metric = ref('frequency')
const lag = ref(0)

const result = ref<CorrelationResult | null>(null)
const loading = ref(false)
const err = ref<string | null>(null)

const metrics = ['frequency', 'gap_mean', 'sum_mean', 'even_fraction']

async function runCorrelation() {
  if (!signalName.value.trim()) return
  loading.value = true
  err.value = null
  result.value = null
  try {
    result.value = await post<CorrelationResult>('/v1/correlations', {
      signal: signalName.value.trim(),
      metric: metric.value,
      lag_draws: lag.value,
    })
  } catch (e) {
    err.value = e instanceof Error ? e.message : 'Request failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <NuxtLink to="/research" class="text-sm text-blue-600 hover:underline mb-4 block">← Research</NuxtLink>
    <h1 class="text-2xl font-bold mb-2">Signal Correlation Explorer</h1>
    <p class="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-1.5 mb-6 inline-block">
      artifact_type: research — correlation results do not imply causation or predictive power.
    </p>

    <div class="flex flex-wrap items-end gap-4 mb-6 text-sm">
      <label class="flex flex-col gap-1">
        Signal name
        <input
          v-model="signalName"
          type="text"
          placeholder="e.g. sp500_close"
          class="border rounded px-3 py-1.5 w-48 focus:outline-none focus:ring-2 focus:ring-blue-400"
          @keydown.enter="runCorrelation"
        />
      </label>
      <label class="flex flex-col gap-1">
        Metric
        <select v-model="metric" class="border rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400">
          <option v-for="m in metrics" :key="m" :value="m">{{ m }}</option>
        </select>
      </label>
      <label class="flex flex-col gap-1">
        Lag (draws)
        <input
          v-model.number="lag"
          type="number"
          min="-100"
          max="100"
          class="border rounded px-2 py-1.5 w-24 focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
      </label>
      <button
        class="px-4 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 self-end"
        :disabled="loading || !signalName.trim()"
        @click="runCorrelation"
      >
        {{ loading ? 'Running…' : 'Run' }}
      </button>
    </div>

    <div v-if="err" class="text-red-600 text-sm mb-4">{{ err }}</div>

    <div v-if="result" class="bg-white rounded-lg border border-gray-200 p-6 max-w-lg text-sm">
      <div class="grid grid-cols-2 gap-3 mb-4">
        <div>
          <div class="text-xs text-gray-400 mb-0.5">Spearman ρ</div>
          <div class="text-xl font-bold tabular-nums">{{ result.rho.toFixed(4) }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-400 mb-0.5">p-value</div>
          <div class="text-xl font-bold tabular-nums">{{ result.p_value.toExponential(2) }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-400 mb-0.5">Effect size</div>
          <div class="tabular-nums">{{ result.effect_size.toFixed(4) }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-400 mb-0.5">Test used</div>
          <div class="font-mono text-xs">{{ result.test_used }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-400 mb-0.5">Sample size</div>
          <div class="tabular-nums">{{ result.sample_size }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-400 mb-0.5">Significant</div>
          <span
            class="px-2 py-0.5 rounded-full text-xs font-medium"
            :class="result.significant ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'"
          >
            {{ result.significant ? 'Yes' : 'No' }}
          </span>
          <span v-if="result.under_powered" class="ml-2 text-xs text-amber-600 font-medium">under-powered</span>
        </div>
      </div>
      <p class="text-xs text-amber-700 border-t border-amber-100 pt-3 mt-3">{{ result.disclaimer }}</p>
    </div>
  </div>
</template>
