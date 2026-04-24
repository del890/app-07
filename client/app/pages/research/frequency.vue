<script setup lang="ts">
import { Bar } from 'vue-chartjs'
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  LinearScale,
  Title,
  Tooltip,
} from 'chart.js'
import type { FrequencyResult } from '~/types/api'

ChartJS.register(Title, Tooltip, CategoryScale, LinearScale, BarElement)

const { get } = useApi()
const { provenance, load: loadProvenance } = useDatasetProvenance()

onMounted(() => loadProvenance())

const windowSize = ref<number | null>(null)
const windowInput = ref<string>('')

const { data, pending, error, refresh } = await useAsyncData<FrequencyResult>(
  'frequency',
  () => get('/v1/statistics/frequency', windowSize.value ? { window: windowSize.value } : {}),
  { watch: [windowSize] },
)

function applyWindow() {
  const n = parseInt(windowInput.value)
  windowSize.value = n > 0 ? n : null
}

function clearWindow() {
  windowInput.value = ''
  windowSize.value = null
}

const chartData = computed(() => {
  if (!data.value) return null
  const sorted = [...data.value.frequencies].sort((a, b) => a.number - b.number)
  return {
    labels: sorted.map((f) => String(f.number)),
    datasets: [
      {
        label: 'Count',
        data: sorted.map((f) => f.count),
        backgroundColor: 'rgba(59,130,246,0.6)',
        borderColor: 'rgba(59,130,246,1)',
        borderWidth: 1,
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  plugins: { title: { display: false } },
  scales: { y: { beginAtZero: true } },
}
</script>

<template>
  <div>
    <NuxtLink to="/research" class="text-sm text-blue-600 hover:underline mb-4 block">← Research</NuxtLink>
    <h1 class="text-2xl font-bold mb-1">Number Frequency</h1>
    <p class="text-xs text-gray-400 mb-4">
      Dataset: {{ provenance?.content_hash?.slice(0, 12) }}
      · Window: {{ data?.meta.window ?? '—' }}
      · {{ data?.meta.window_size ?? 0 }} draws
    </p>

    <!-- Window selector -->
    <div class="flex items-center gap-2 mb-6">
      <input
        v-model="windowInput"
        type="number"
        min="1"
        placeholder="Rolling window (draws)"
        class="border rounded px-3 py-1.5 text-sm w-48 focus:outline-none focus:ring-2 focus:ring-blue-400"
        @keydown.enter="applyWindow"
      />
      <button
        class="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
        @click="applyWindow"
      >Apply</button>
      <button
        v-if="windowSize"
        class="px-3 py-1.5 bg-gray-200 text-sm rounded hover:bg-gray-300"
        @click="clearWindow"
      >Full history</button>
    </div>

    <div v-if="pending" class="text-gray-400 py-8 text-center">Loading…</div>
    <div v-else-if="error" class="text-red-600 py-4">{{ error.message }}</div>
    <template v-else-if="data && chartData">
      <div class="bg-white rounded-lg border border-gray-200 p-4 mb-6">
        <Bar :data="chartData" :options="chartOptions" />
      </div>

      <!-- Table -->
      <div class="overflow-x-auto bg-white rounded-lg border border-gray-200">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-2 text-left font-medium">#</th>
              <th class="px-4 py-2 text-right font-medium">Count</th>
              <th class="px-4 py-2 text-right font-medium">Share</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="f in [...data.frequencies].sort((a, b) => a.number - b.number)"
              :key="f.number"
              class="border-b border-gray-100 hover:bg-gray-50"
            >
              <td class="px-4 py-2 font-mono">{{ f.number }}</td>
              <td class="px-4 py-2 text-right tabular-nums">{{ f.count }}</td>
              <td class="px-4 py-2 text-right tabular-nums">{{ (f.share * 100).toFixed(2) }}%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
