<script setup lang="ts">
import type { GapResult } from '~/types/api'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'

const { get } = useApi()

const hotFactor = ref(0.5)
const coldFactor = ref(2.0)

const { data, pending, error } = await useAsyncData<GapResult>(
  'gaps',
  () => get('/v1/statistics/gaps', { hot_factor: hotFactor.value, cold_factor: coldFactor.value }),
  { watch: [hotFactor, coldFactor] },
)

const classColor: Record<string, string> = {
  hot: 'bg-destructive/15 text-destructive',
  cold: 'bg-primary/10 text-primary',
  neutral: 'bg-muted text-muted-foreground',
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <Button variant="ghost" as-child class="-ml-3 mb-1">
        <NuxtLink to="/research">← Pesquisa</NuxtLink>
      </Button>
      <h1 class="text-2xl font-bold">Análise de Intervalos Quente / Frio</h1>
      <p class="text-xs text-muted-foreground">
        Limiar — fator quente: {{ hotFactor }}× · fator frio: {{ coldFactor }}×
        <span class="ml-2 italic">(quente = intervalo_atual &lt; média × fator_quente; frio = intervalo_atual &gt; média × fator_frio)</span>
      </p>
    </div>

    <!-- Threshold controls -->
    <div class="flex flex-wrap items-center gap-4 text-sm">
      <label class="flex items-center gap-2">
        Fator quente
        <Input v-model.number="hotFactor" type="number" step="0.1" min="0.1" max="1.0" class="w-20" />
      </label>
      <label class="flex items-center gap-2">
        Fator frio
        <Input v-model.number="coldFactor" type="number" step="0.1" min="1.1" max="10.0" class="w-20" />
      </label>
    </div>

    <div v-if="pending" class="text-muted-foreground py-8 text-center">Carregando…</div>
    <div v-else-if="error" class="text-destructive py-4">{{ error.message }}</div>
    <div v-else-if="data" class="overflow-x-auto bg-card rounded-lg border">
      <table class="w-full text-sm">
        <thead class="bg-muted border-b">
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
            class="border-b hover:bg-muted/30"
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
