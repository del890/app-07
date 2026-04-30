<script setup lang="ts">
import type { GapResult } from '~/types/api'

const { get } = useApi()

const hotFactor = ref(0.5)
const coldFactor = ref(2.0)

const { data, pending, error } = await useAsyncData<GapResult>(
  'gaps',
  () => get('/v1/statistics/gaps', { hot_factor: hotFactor.value, cold_factor: coldFactor.value }),
  { watch: [hotFactor, coldFactor] },
)

const classColor: Record<string, string> = {
  hot: 'bg-red-100 text-red-700',
  cold: 'bg-blue-100 text-blue-700',
  neutral: 'bg-gray-100 text-gray-600',
}
</script>

<template>
  <div>
    <NuxtLink to="/research" class="text-sm text-blue-600 hover:underline mb-4 block">← Pesquisa</NuxtLink>
    <h1 class="text-2xl font-bold mb-1">Análise de Intervalos Quente / Frio</h1>
    <p class="text-xs text-gray-400 mb-4">
      Limiar — fator quente: {{ hotFactor }}× · fator frio: {{ coldFactor }}×
      <span class="ml-2 italic">(quente = intervalo_atual &lt; média × fator_quente; frio = intervalo_atual &gt; média × fator_frio)</span>
    </p>

    <!-- Threshold controls -->
    <div class="flex flex-wrap items-center gap-4 mb-6 text-sm">
      <label class="flex items-center gap-2">
        Fator quente
        <input v-model.number="hotFactor" type="number" step="0.1" min="0.1" max="1.0"
          class="border rounded px-2 py-1 w-20 focus:outline-none focus:ring-2 focus:ring-blue-400" />
      </label>
      <label class="flex items-center gap-2">
        Fator frio
        <input v-model.number="coldFactor" type="number" step="0.1" min="1.1" max="10.0"
          class="border rounded px-2 py-1 w-20 focus:outline-none focus:ring-2 focus:ring-blue-400" />
      </label>
    </div>

    <div v-if="pending" class="text-gray-400 py-8 text-center">Carregando…</div>
    <div v-else-if="error" class="text-red-600 py-4">{{ error.message }}</div>
    <div v-else-if="data" class="overflow-x-auto bg-white rounded-lg border border-gray-200">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="px-4 py-2 text-left font-medium">#</th>
            <th class="px-4 py-2 text-right font-medium">Intervalo Atual</th>
            <th class="px-4 py-2 text-right font-medium">Intervalo Médio</th>
            <th class="px-4 py-2 text-right font-medium">Intervalo Máximo</th>
            <th class="px-4 py-2 text-center font-medium">Classificação</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="g in data.gaps"
            :key="g.number"
            class="border-b border-gray-100 hover:bg-gray-50"
          >
            <td class="px-4 py-2 font-mono">{{ g.number }}</td>
            <td class="px-4 py-2 text-right tabular-nums">{{ g.current_gap }}</td>
            <td class="px-4 py-2 text-right tabular-nums">{{ g.mean_gap.toFixed(1) }}</td>
            <td class="px-4 py-2 text-right tabular-nums">{{ g.max_gap }}</td>
            <td class="px-4 py-2 text-center">
              <span class="px-2 py-0.5 rounded-full text-xs font-medium" :class="classColor[g.classification]">
                {{ g.classification }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
