<script setup lang="ts">
import { Button } from '~/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import type {
  DrawsPage,
  HistoricalDraw,
  PredictionHistoryPage,
  ScenarioPathPrediction,
  StoredNextDraw,
  StoredScenarioPath,
} from '~/types/api'

const { getDraws, getPredictionHistory } = useApi()

// ── Tab state ────────────────────────────────────────────────────────────
type Tab = 'draws' | 'generated'
const activeTab = ref<Tab>('draws')

// ── Historical draws state ────────────────────────────────────────────────
const drawsPage = ref(1)
const drawsPageSize = 50
const draws = ref<HistoricalDraw[]>([])
const drawsTotal = ref(0)
const drawsLoading = ref(false)
const drawsError = ref<string | null>(null)

async function loadDraws(page: number) {
  drawsLoading.value = true
  drawsError.value = null
  try {
    const data: DrawsPage = await getDraws(page, drawsPageSize)
    draws.value = data.draws
    drawsTotal.value = data.total
    drawsPage.value = data.page
  } catch (err) {
    drawsError.value = err instanceof Error ? err.message : 'Falha ao carregar sorteios'
  } finally {
    drawsLoading.value = false
  }
}

const drawsTotalPages = computed(() => Math.ceil(drawsTotal.value / drawsPageSize))

// ── Generated predictions state ───────────────────────────────────────────
const predPage = ref(1)
const predPageSize = 20
const predictions = ref<Array<StoredNextDraw | StoredScenarioPath>>([])
const predTotal = ref(0)
const predLoading = ref(false)
const predError = ref<string | null>(null)
const predKindFilter = ref<'next_draw' | 'scenario_path' | ''>('')

async function loadPredictions(page: number) {
  predLoading.value = true
  predError.value = null
  try {
    const kind = predKindFilter.value || undefined
    const data: PredictionHistoryPage = await getPredictionHistory(kind, page, predPageSize)
    predictions.value = data.items as Array<StoredNextDraw | StoredScenarioPath>
    predTotal.value = data.total
    predPage.value = data.page
  } catch (err) {
    predError.value = err instanceof Error ? err.message : 'Falha ao carregar previsões'
  } finally {
    predLoading.value = false
  }
}

const predTotalPages = computed(() => Math.ceil(predTotal.value / predPageSize))

function onKindFilterChange() {
  predPage.value = 1
  loadPredictions(1)
}

// ── Helpers ───────────────────────────────────────────────────────────────
function isNextDraw(item: StoredNextDraw | StoredScenarioPath): item is StoredNextDraw {
  return item.kind === 'next_draw'
}
function isScenarioPath(item: StoredNextDraw | StoredScenarioPath): item is StoredScenarioPath {
  return item.kind === 'scenario_path'
}

/** Normalise a scenario prediction – handles both the legacy field names
 *  (steps / predicted_numbers / step_confidence) and the current canonical
 *  names (path / numbers / confidence / horizon). */
function normalizeScenario(item: StoredScenarioPath): ScenarioPathPrediction {
  const pred = item.prediction as unknown as Record<string, unknown>
  const rawSteps = (pred.path ?? pred.steps ?? []) as Record<string, unknown>[]
  return {
    horizon: (pred.horizon as number | undefined) ?? rawSteps.length,
    path: rawSteps.map((s) => ({
      step: s.step as number,
      numbers: ((s.numbers ?? s.predicted_numbers) as number[]) ?? [],
      confidence: ((s.confidence ?? s.step_confidence) as number) ?? 0.5,
      explanation: (s.explanation as string) ?? '',
    })),
    calibrated: pred.calibrated as boolean,
    provenance: pred.provenance as ScenarioPathPrediction['provenance'],
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// ── Initialise ────────────────────────────────────────────────────────────
loadDraws(1)
loadPredictions(1)

watch(activeTab, (tab) => {
  if (tab === 'draws' && draws.value.length === 0) loadDraws(1)
  if (tab === 'generated' && predictions.value.length === 0) loadPredictions(1)
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <Button variant="ghost" as-child class="-ml-3 mb-1">
        <NuxtLink to="/play">← Play</NuxtLink>
      </Button>
      <h1 class="text-2xl font-bold">Histórico</h1>
    </div>

    <!-- Tab bar -->
    <div class="flex gap-1 border-b">
      <button
        class="px-5 py-2.5 text-sm font-medium border-b-2 transition-colors"
        :class="activeTab === 'draws'
          ? 'border-primary text-primary'
          : 'border-transparent text-muted-foreground hover:text-foreground'"
        @click="activeTab = 'draws'"
      >
        Sorteios Históricos
        <span class="ml-1.5 text-xs text-muted-foreground">({{ drawsTotal }})</span>
      </button>
      <button
        class="px-5 py-2.5 text-sm font-medium border-b-2 transition-colors"
        :class="activeTab === 'generated'
          ? 'border-primary text-primary'
          : 'border-transparent text-muted-foreground hover:text-foreground'"
        @click="activeTab = 'generated'"
      >
        Sorteios Gerados
        <span class="ml-1.5 text-xs text-muted-foreground">({{ predTotal }})</span>
      </button>
    </div>

    <!-- ── Historic Draws tab ─────────────────────────────────────────── -->
    <div v-if="activeTab === 'draws'">
      <div v-if="drawsLoading" class="text-sm text-muted-foreground">Carregando…</div>
      <div v-else-if="drawsError" class="text-sm text-destructive">{{ drawsError }}</div>
      <div v-else>
        <!-- Table -->
        <div class="overflow-x-auto rounded-lg border">
          <table class="min-w-full text-sm">
            <thead class="bg-muted text-xs text-muted-foreground uppercase tracking-wide">
              <tr>
                <th class="px-4 py-3 text-left w-12">#</th>
                <th class="px-4 py-3 text-left w-28">Data</th>
                <th class="px-4 py-3 text-left">Números</th>
              </tr>
            </thead>
            <tbody class="divide-y bg-card">
              <tr v-for="draw in draws" :key="draw.original_id" class="hover:bg-muted/30">
                <td class="px-4 py-2.5 text-muted-foreground font-mono text-xs">{{ draw.original_id }}</td>
                <td class="px-4 py-2.5 text-foreground whitespace-nowrap">{{ formatDate(draw.date) }}</td>
                <td class="px-4 py-2.5">
                  <div class="flex flex-wrap gap-1">
                    <span
                      v-for="n in draw.numbers"
                      :key="n"
                      class="w-7 h-7 flex items-center justify-center rounded-full bg-accent text-accent-foreground font-semibold text-xs"
                    >
                      {{ n }}
                    </span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="drawsTotalPages > 1" class="flex items-center justify-between mt-4 text-sm">
          <span class="text-muted-foreground">
            Página {{ drawsPage }} de {{ drawsTotalPages }}
            <span class="ml-2 text-muted-foreground/60">({{ drawsTotal }} total)</span>
          </span>
          <div class="flex gap-2">
            <Button variant="outline" size="sm" :disabled="drawsPage <= 1" @click="loadDraws(drawsPage - 1)">←</Button>
            <Button variant="outline" size="sm" :disabled="drawsPage >= drawsTotalPages" @click="loadDraws(drawsPage + 1)">→</Button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Generated Draws tab ────────────────────────────────────────── -->
    <div v-if="activeTab === 'generated'">
      <!-- Filter -->
      <div class="flex items-center gap-3 mb-4">
        <span class="text-sm text-muted-foreground">Filtrar:</span>
        <Select v-model="predKindFilter" @update:model-value="onKindFilterChange">
          <SelectTrigger class="w-48">
            <SelectValue placeholder="Todos os tipos" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os tipos</SelectItem>
            <SelectItem value="next_draw">Próximo Sorteio</SelectItem>
            <SelectItem value="scenario_path">Caminho de Cenário</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div v-if="predLoading" class="text-sm text-muted-foreground">Carregando…</div>
      <div v-else-if="predError" class="text-sm text-destructive">{{ predError }}</div>
      <div v-else-if="predictions.length === 0" class="text-sm text-muted-foreground py-8 text-center">
        Nenhum sorteio gerado ainda. Vá para
        <NuxtLink to="/play/next-draw" class="text-primary hover:underline">Sugerir Próximo Sorteio</NuxtLink>
        ou
        <NuxtLink to="/play/scenario" class="text-primary hover:underline">Caminho de Cenário</NuxtLink>
        para gerar alguns.
      </div>
      <div v-else class="space-y-4">
        <!-- Next-draw entries -->
        <template v-for="item in predictions" :key="item.id">
          <!-- Next Draw card -->
          <div
            v-if="isNextDraw(item)"
            class="bg-card rounded-lg border p-4"
          >
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-2">
                <span class="text-xs font-semibold text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-full">
                  Próximo Sorteio
                </span>
                <ConfidenceBadge :confidence="item.prediction.confidence" />
              </div>
              <span class="text-xs text-muted-foreground">{{ formatDateTime(item.stored_at) }}</span>
            </div>
            <div class="flex flex-wrap gap-1.5 mb-3">
              <span
                v-for="n in item.prediction.numbers"
                :key="n"
                class="w-8 h-8 flex items-center justify-center rounded-full bg-accent text-accent-foreground font-bold text-xs"
              >
                {{ n }}
              </span>
            </div>
            <p class="text-xs text-muted-foreground line-clamp-2">{{ item.prediction.explanation }}</p>
          </div>

          <!-- Scenario Path card -->
          <div
            v-else-if="isScenarioPath(item)"
            class="bg-card rounded-lg border p-4"
          >
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-2">
                <span class="text-xs font-semibold text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-full">
                  Cenário ({{ normalizeScenario(item).horizon }} sorteios)
                </span>
              </div>
              <span class="text-xs text-muted-foreground">{{ formatDateTime(item.stored_at) }}</span>
            </div>
            <div class="space-y-2">
              <div
                v-for="step in normalizeScenario(item).path"
                :key="step.step"
                class="flex items-center gap-3"
              >
                <span class="text-xs text-primary font-medium w-12 shrink-0">+{{ step.step }}</span>
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="n in step.numbers"
                    :key="n"
                    class="w-7 h-7 flex items-center justify-center rounded-full bg-accent text-accent-foreground font-bold text-xs"
                  >
                    {{ n }}
                  </span>
                </div>
                <ConfidenceBadge :confidence="step.confidence" />
              </div>
            </div>
          </div>
        </template>

        <!-- Pagination -->
        <div v-if="predTotalPages > 1" class="flex items-center justify-between mt-2 text-sm">
          <span class="text-muted-foreground">
            Página {{ predPage }} de {{ predTotalPages }}
            <span class="ml-2 text-muted-foreground/60">({{ predTotal }} total)</span>
          </span>
          <div class="flex gap-2">
            <Button variant="outline" size="sm" :disabled="predPage <= 1" @click="loadPredictions(predPage - 1)">←</Button>
            <Button variant="outline" size="sm" :disabled="predPage >= predTotalPages" @click="loadPredictions(predPage + 1)">→</Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
