<script setup lang="ts">
import { Bar } from 'vue-chartjs'
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  LinearScale,
  Tooltip,
} from 'chart.js'
import type { StructuralResult } from '~/types/api'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const { get } = useApi()

const { data, pending, error } = await useAsyncData<StructuralResult>(
  'structural',
  () => get('/v1/statistics/structural'),
)

function toChartData(bins: { value: number; count: number }[], label: string) {
  return {
    labels: bins.map((b) => String(b.value)),
    datasets: [{ label, data: bins.map((b) => b.count), backgroundColor: 'rgba(99,102,241,0.6)' }],
  }
}

const chartOptions = { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
</script>

<template>
  <div>
    <NuxtLink to="/research" class="text-sm text-blue-600 hover:underline mb-4 block">← Research</NuxtLink>
    <h1 class="text-2xl font-bold mb-6">Structural Distributions</h1>

    <div v-if="pending" class="text-gray-400 py-8 text-center">Loading…</div>
    <div v-else-if="error" class="text-red-600 py-4">{{ error.message }}</div>
    <template v-else-if="data">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <h2 class="font-semibold mb-3 text-gray-700">Draw Sum Distribution
            <span class="text-xs font-normal text-gray-400 ml-1">(min {{ data.sum_min }}, max {{ data.sum_max }})</span>
          </h2>
          <Bar :data="toChartData(data.sum_histogram, 'Count')" :options="chartOptions" />
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <h2 class="font-semibold mb-3 text-gray-700">Even Number Count per Draw</h2>
          <Bar :data="toChartData(data.even_count_histogram, 'Count')" :options="chartOptions" />
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <h2 class="font-semibold mb-3 text-gray-700">Quintile Distribution</h2>
          <Bar :data="toChartData(data.quintile_histogram, 'Count')" :options="chartOptions" />
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <h2 class="font-semibold mb-3 text-gray-700">Min Number per Draw</h2>
          <Bar :data="toChartData(data.min_number_histogram, 'Count')" :options="chartOptions" />
        </div>
      </div>
    </template>
  </div>
</template>
