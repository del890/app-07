<script setup lang="ts">
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
    drawsError.value = err instanceof Error ? err.message : 'Failed to load draws'
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
    predError.value = err instanceof Error ? err.message : 'Failed to load predictions'
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
  <div>
    <NuxtLink to="/play" class="text-sm text-blue-600 hover:underline mb-4 block">← Play</NuxtLink>
    <h1 class="text-2xl font-bold mb-6">History</h1>

    <!-- Tab bar -->
    <div class="flex gap-1 mb-6 border-b border-gray-200">
      <button
        class="px-5 py-2.5 text-sm font-medium border-b-2 transition-colors"
        :class="activeTab === 'draws'
          ? 'border-purple-600 text-purple-700'
          : 'border-transparent text-gray-500 hover:text-gray-700'"
        @click="activeTab = 'draws'"
      >
        Historic Draws
        <span class="ml-1.5 text-xs text-gray-400">({{ drawsTotal }})</span>
      </button>
      <button
        class="px-5 py-2.5 text-sm font-medium border-b-2 transition-colors"
        :class="activeTab === 'generated'
          ? 'border-indigo-600 text-indigo-700'
          : 'border-transparent text-gray-500 hover:text-gray-700'"
        @click="activeTab = 'generated'"
      >
        Generated Draws
        <span class="ml-1.5 text-xs text-gray-400">({{ predTotal }})</span>
      </button>
    </div>

    <!-- ── Historic Draws tab ─────────────────────────────────────────── -->
    <div v-if="activeTab === 'draws'">
      <div v-if="drawsLoading" class="text-sm text-gray-400">Loading…</div>
      <div v-else-if="drawsError" class="text-sm text-red-500">{{ drawsError }}</div>
      <div v-else>
        <!-- Table -->
        <div class="overflow-x-auto rounded-lg border border-gray-200">
          <table class="min-w-full text-sm">
            <thead class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
              <tr>
                <th class="px-4 py-3 text-left w-12">#</th>
                <th class="px-4 py-3 text-left w-28">Date</th>
                <th class="px-4 py-3 text-left">Numbers</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 bg-white">
              <tr v-for="draw in draws" :key="draw.original_id" class="hover:bg-gray-50">
                <td class="px-4 py-2.5 text-gray-400 font-mono text-xs">{{ draw.original_id }}</td>
                <td class="px-4 py-2.5 text-gray-600 whitespace-nowrap">{{ formatDate(draw.date) }}</td>
                <td class="px-4 py-2.5">
                  <div class="flex flex-wrap gap-1">
                    <span
                      v-for="n in draw.numbers"
                      :key="n"
                      class="w-7 h-7 flex items-center justify-center rounded-full bg-purple-100 text-purple-800 font-semibold text-xs"
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
          <span class="text-gray-500">
            Page {{ drawsPage }} of {{ drawsTotalPages }}
            <span class="ml-2 text-gray-400">({{ drawsTotal }} total)</span>
          </span>
          <div class="flex gap-2">
            <button
              :disabled="drawsPage <= 1"
              class="px-3 py-1.5 rounded border text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
              @click="loadDraws(drawsPage - 1)"
            >
              ←
            </button>
            <button
              :disabled="drawsPage >= drawsTotalPages"
              class="px-3 py-1.5 rounded border text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
              @click="loadDraws(drawsPage + 1)"
            >
              →
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Generated Draws tab ────────────────────────────────────────── -->
    <div v-if="activeTab === 'generated'">
      <!-- Filter -->
      <div class="flex items-center gap-3 mb-4">
        <span class="text-sm text-gray-500">Filter:</span>
        <select
          v-model="predKindFilter"
          class="text-sm border rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-300"
          @change="onKindFilterChange"
        >
          <option value="">All types</option>
          <option value="next_draw">Next Draw</option>
          <option value="scenario_path">Scenario Path</option>
        </select>
      </div>

      <div v-if="predLoading" class="text-sm text-gray-400">Loading…</div>
      <div v-else-if="predError" class="text-sm text-red-500">{{ predError }}</div>
      <div v-else-if="predictions.length === 0" class="text-sm text-gray-400 py-8 text-center">
        No generated draws yet. Go to
        <NuxtLink to="/play/next-draw" class="text-purple-600 hover:underline">Suggest Next Draw</NuxtLink>
        or
        <NuxtLink to="/play/scenario" class="text-indigo-600 hover:underline">Scenario Path</NuxtLink>
        to generate some.
      </div>
      <div v-else class="space-y-4">
        <!-- Next-draw entries -->
        <template v-for="item in predictions" :key="item.id">
          <!-- Next Draw card -->
          <div
            v-if="isNextDraw(item)"
            class="bg-white rounded-lg border border-gray-200 p-4"
          >
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-2">
                <span class="text-xs font-semibold text-purple-700 bg-purple-50 border border-purple-200 px-2 py-0.5 rounded-full">
                  Next Draw
                </span>
                <ConfidenceBadge :confidence="item.prediction.confidence" />
              </div>
              <span class="text-xs text-gray-400">{{ formatDateTime(item.stored_at) }}</span>
            </div>
            <div class="flex flex-wrap gap-1.5 mb-3">
              <span
                v-for="n in item.prediction.numbers"
                :key="n"
                class="w-8 h-8 flex items-center justify-center rounded-full bg-purple-100 text-purple-800 font-bold text-xs"
              >
                {{ n }}
              </span>
            </div>
            <p class="text-xs text-gray-500 line-clamp-2">{{ item.prediction.explanation }}</p>
          </div>

          <!-- Scenario Path card -->
          <div
            v-else-if="isScenarioPath(item)"
            class="bg-white rounded-lg border border-gray-200 p-4"
          >
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-2">
                <span class="text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded-full">
                  Scenario ({{ normalizeScenario(item).horizon }} draws)
                </span>
              </div>
              <span class="text-xs text-gray-400">{{ formatDateTime(item.stored_at) }}</span>
            </div>
            <div class="space-y-2">
              <div
                v-for="step in normalizeScenario(item).path"
                :key="step.step"
                class="flex items-center gap-3"
              >
                <span class="text-xs text-indigo-500 font-medium w-12 shrink-0">+{{ step.step }}</span>
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="n in step.numbers"
                    :key="n"
                    class="w-7 h-7 flex items-center justify-center rounded-full bg-indigo-50 text-indigo-800 font-bold text-xs"
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
          <span class="text-gray-500">
            Page {{ predPage }} of {{ predTotalPages }}
            <span class="ml-2 text-gray-400">({{ predTotal }} total)</span>
          </span>
          <div class="flex gap-2">
            <button
              :disabled="predPage <= 1"
              class="px-3 py-1.5 rounded border text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
              @click="loadPredictions(predPage - 1)"
            >
              ←
            </button>
            <button
              :disabled="predPage >= predTotalPages"
              class="px-3 py-1.5 rounded border text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
              @click="loadPredictions(predPage + 1)"
            >
              →
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
