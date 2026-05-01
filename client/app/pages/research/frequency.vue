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
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'

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
        label: 'Contagem',
        data: sorted.map((f) => f.count),
        backgroundColor: 'hsl(262 52% 47% / 0.6)',
        borderColor: 'hsl(262 52% 47%)',
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
  <div class="space-y-6">
    <div>
      <Button variant="ghost" as-child class="-ml-3 mb-1">
        <NuxtLink to="/research">← Pesquisa</NuxtLink>
      </Button>
      <h1 class="text-2xl font-bold">Frequência por Número</h1>
      <p class="text-xs text-muted-foreground">
        Conjunto de dados: {{ provenance?.content_hash?.slice(0, 12) }}
        · Janela: {{ data?.meta.window ?? '—' }}
        · {{ data?.meta.window_size ?? 0 }} sorteios
      </p>
    </div>

    <!-- Window selector -->
    <div class="flex items-center gap-2">
      <Input
        v-model="windowInput"
        type="number"
        min="1"
        placeholder="Janela deslizante (sorteios)"
        class="w-48"
        @keydown.enter="applyWindow"
      />
      <Button size="sm" @click="applyWindow">Aplicar</Button>
      <Button v-if="windowSize" variant="outline" size="sm" @click="clearWindow">Histórico completo</Button>
    </div>

    <div v-if="pending" class="text-muted-foreground py-8 text-center">Carregando…</div>
    <div v-else-if="error" class="text-destructive py-4">{{ error.message }}</div>
    <template v-else-if="data && chartData">
      <div class="bg-card rounded-lg border p-4">
        <Bar :data="chartData" :options="chartOptions" />
      </div>

      <!-- Table -->
      <div class="overflow-x-auto bg-card rounded-lg border">
        <table class="w-full text-sm">
          <thead class="bg-muted border-b">
            <tr>
              <th class="px-4 py-2 text-left font-medium">#</th>
              <th class="px-4 py-2 text-right font-medium">Contagem</th>
              <th class="px-4 py-2 text-right font-medium">Participação</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="f in [...data.frequencies].sort((a, b) => a.number - b.number)"
              :key="f.number"
              class="border-b hover:bg-muted/30"
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
