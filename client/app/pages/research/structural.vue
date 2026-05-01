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
import { Button } from '~/components/ui/button'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const { get } = useApi()

const { data, pending, error } = await useAsyncData<StructuralResult>(
  'structural',
  () => get('/v1/statistics/structural'),
)

function toChartData(bins: { value: number; count: number }[], label: string) {
  return {
    labels: bins.map((b) => String(b.value)),
    datasets: [{ label, data: bins.map((b) => b.count), backgroundColor: 'hsl(262 52% 47% / 0.6)' }],
  }
}

const chartOptions = { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
</script>

<template>
  <div class="space-y-6">
    <div>
      <Button variant="ghost" as-child class="-ml-3 mb-1">
        <NuxtLink to="/research">← Pesquisa</NuxtLink>
      </Button>
      <h1 class="text-2xl font-bold">Distribuições Estruturais</h1>
    </div>

    <div v-if="pending" class="text-muted-foreground py-8 text-center">Carregando…</div>
    <div v-else-if="error" class="text-destructive py-4">{{ error.message }}</div>
    <template v-else-if="data">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-card rounded-lg border p-4">
          <h2 class="font-semibold mb-3">Distribuição da Soma do Sorteio
            <span class="text-xs font-normal text-muted-foreground ml-1">(mín {{ data.sum_min }}, máx {{ data.sum_max }})</span>
          </h2>
          <Bar :data="toChartData(data.sum_histogram, 'Contagem')" :options="chartOptions" />
        </div>
        <div class="bg-card rounded-lg border p-4">
          <h2 class="font-semibold mb-3">Contagem de Números Pares por Sorteio</h2>
          <Bar :data="toChartData(data.even_count_histogram, 'Contagem')" :options="chartOptions" />
        </div>
        <div class="bg-card rounded-lg border p-4">
          <h2 class="font-semibold mb-3">Distribuição por Quintil</h2>
          <Bar :data="toChartData(data.quintile_histogram, 'Contagem')" :options="chartOptions" />
        </div>
        <div class="bg-card rounded-lg border p-4">
          <h2 class="font-semibold mb-3">Número Mínimo por Sorteio</h2>
          <Bar :data="toChartData(data.min_number_histogram, 'Contagem')" :options="chartOptions" />
        </div>
      </div>
    </template>
  </div>
</template>
