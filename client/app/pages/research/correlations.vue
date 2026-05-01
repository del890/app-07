<script setup lang="ts">
import type { CorrelationResult } from '~/types/api'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'

interface SignalInfo {
  name: string
  cadence: string
  unit: string
  source: string
  description: string
  point_count: number
  first_date: string
  last_date: string
}

const { get, post } = useApi()

const signalName = ref('')
const metric = ref('sum')
const lag = ref(0)

const availableSignals = ref<SignalInfo[]>([])
onMounted(async () => {
  try {
    const data = await get<{ signals: SignalInfo[] }>('/v1/correlations/signals')
    availableSignals.value = data.signals
  } catch {
    // silently ignore — signals panel is optional
  }
})

const result = ref<CorrelationResult | null>(null)
const loading = ref(false)
const err = ref<string | null>(null)

const metrics: { label: string; name: string; kind: 'continuous' | 'binary' }[] = [
  { label: 'Soma', name: 'sum', kind: 'continuous' },
  { label: 'Contagem de pares', name: 'even_count', kind: 'continuous' },
  { label: 'Número presente', name: 'number_present', kind: 'binary' },
]

async function runCorrelation() {
  if (!signalName.value.trim()) return
  loading.value = true
  err.value = null
  result.value = null
  const selectedMetric = metrics.find(m => m.name === metric.value)
  if (!selectedMetric) return
  try {
    result.value = await post<CorrelationResult>('/v1/correlations', {
      signal: signalName.value.trim(),
      metric: { name: selectedMetric.name, kind: selectedMetric.kind },
      lag_draws: lag.value,
    })
  } catch (e) {
    err.value = e instanceof Error ? e.message : 'Requisição falhou'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <Button variant="ghost" as-child class="-ml-3 mb-1">
        <NuxtLink to="/research">← Pesquisa</NuxtLink>
      </Button>
      <h1 class="text-2xl font-bold">Explorador de Correlação de Sinais</h1>
      <p class="text-sm text-muted-foreground mt-1 max-w-prose">
        Um <strong>sinal</strong> é uma série temporal externa — por exemplo, o índice Ibovespa, o preço do dólar ou a fase da lua —
        carregada como um arquivo CSV ou JSON no serviço. Esta página mede se existe correlação estatística entre os valores
        desse sinal e uma métrica dos sorteios da Lotofácil (ex.: soma dos números sorteados).
      </p>
      <p class="text-xs text-warning-foreground bg-warning/10 border border-warning/30 rounded px-3 py-1.5 mt-2 inline-block">
        artifact_type: research — resultados de correlação não implicam causalidade ou poder preditivo.
      </p>
    </div>

    <div class="flex flex-wrap items-end gap-4 text-sm">
      <label class="flex flex-col gap-1">
        Nome do sinal
        <Input
          v-model="signalName"
          type="text"
          placeholder="ex: sp500_close"
          class="w-48"
          @keydown.enter="runCorrelation"
        />
      </label>
      <label class="flex flex-col gap-1">
        Métrica
        <Select v-model="metric">
          <SelectTrigger class="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="m in metrics" :key="m.name" :value="m.name">{{ m.label }}</SelectItem>
          </SelectContent>
        </Select>
      </label>
      <label class="flex flex-col gap-1">
        Defasagem (sorteios)
        <Input v-model.number="lag" type="number" min="-100" max="100" class="w-24" />
      </label>
      <Button
        class="self-end"
        :disabled="loading || !signalName.trim()"
        @click="runCorrelation"
      >
        {{ loading ? 'Executando…' : 'Executar' }}
      </Button>
    </div>

    <div v-if="err" class="text-destructive text-sm">{{ err }}</div>

    <!-- Signals available in the service -->
    <div v-if="availableSignals.length > 0" class="space-y-2">
      <p class="text-xs font-medium text-muted-foreground uppercase tracking-wide">Sinais disponíveis</p>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="s in availableSignals"
          :key="s.name"
          type="button"
          class="group flex flex-col items-start gap-0.5 rounded-lg border border-border bg-card px-3 py-2 text-left text-xs hover:border-primary/50 hover:bg-accent transition-colors"
          @click="signalName = s.name"
        >
          <span class="font-mono font-semibold group-hover:text-primary transition-colors">{{ s.name }}</span>
          <span class="text-muted-foreground">{{ s.source }} · {{ s.cadence }} · {{ s.point_count }} pontos</span>
          <span class="text-muted-foreground/70">{{ s.first_date }} → {{ s.last_date }}</span>
        </button>
      </div>
    </div>
    <div v-else-if="availableSignals.length === 0 && !err" class="text-xs text-muted-foreground">
      Nenhum sinal registrado no serviço. Adicione arquivos CSV/JSON em <code class="font-mono">service/signals/</code> e reinicie.
    </div>

    <div v-if="result" class="bg-card rounded-lg border p-6 max-w-lg text-sm">
      <div class="grid grid-cols-2 gap-3 mb-4">
        <div>
          <div class="text-xs text-muted-foreground mb-0.5">Tamanho do efeito</div>
          <div class="text-xl font-bold tabular-nums">{{ result.effect_size.toFixed(4) }}</div>
        </div>
        <div>
          <div class="text-xs text-muted-foreground mb-0.5">p-value</div>
          <div class="text-xl font-bold tabular-nums">{{ result.p_value.toExponential(2) }}</div>
        </div>
        <div>
          <div class="text-xs text-muted-foreground mb-0.5">Teste utilizado</div>
          <div class="font-mono text-xs">{{ result.test }}</div>
        </div>
        <div>
          <div class="text-xs text-muted-foreground mb-0.5">Tamanho da amostra</div>
          <div class="tabular-nums">{{ result.sample_size }}</div>
        </div>
        <div>
          <div class="text-xs text-muted-foreground mb-0.5">Significativo</div>
          <span
            class="px-2 py-0.5 rounded-full text-xs font-medium"
            :class="result.significant ? 'bg-success/15 text-success' : 'bg-muted text-muted-foreground'"
          >
            {{ result.significant ? 'Sim' : 'Não' }}
          </span>
          <span v-if="result.under_powered" class="ml-2 text-xs text-warning-foreground font-medium">baixa potência</span>
        </div>
      </div>
      <p class="text-xs text-warning-foreground border-t border-warning/20 pt-3 mt-3">{{ result.disclaimer }}</p>
    </div>
  </div>
</template>
