<script setup lang="ts">
useHead({ title: 'Admin — Pesquisa Lotofácil' })

// ── Types ────────────────────────────────────────────────────────────────────

interface ReadinessCheck {
  name: string
  ok: boolean
  required: boolean
  detail: string
  extra: Record<string, unknown>
}

interface ReadinessResponse {
  ok: boolean
  version: string
  checks: ReadinessCheck[]
}

interface CalibrationResult {
  ok: boolean
  last_calibrated_at: string | null
  eval_metrics: {
    brier_score_raw: number | null
    brier_score_calibrated: number | null
    log_loss_raw: number | null
    log_loss_calibrated: number | null
    n_eval_rows: number
  } | null
}

// ── State ─────────────────────────────────────────────────────────────────────

const config = useRuntimeConfig()
const apiBase = config.public.apiBase as string

// Readiness
const readiness = ref<ReadinessResponse | null>(null)
const readinessError = ref<string | null>(null)
const loadingReadiness = ref(false)

// Calibration
const calibrationStatus = ref<CalibrationResult | null>(null)
const calibrating = ref(false)
const calibrationError = ref<string | null>(null)
const calibrationDone = ref(false)

// Simulated progress phases while the sync endpoint runs
const progressPhases = ['Preparando conjunto de dados…', 'Treinando modelo…', 'Calibrando pontuações…', 'Avaliando hold-out…', 'Finalizando…']
const currentPhase = ref('')
const progressPct = ref(0)
let phaseTimer: ReturnType<typeof setInterval> | null = null

function startProgressSimulation() {
  let step = 0
  progressPct.value = 0
  currentPhase.value = progressPhases[0]
  phaseTimer = setInterval(() => {
    step++
    const pct = Math.min(step * 18, 90) // never reach 100 — that's set on completion
    progressPct.value = pct
    currentPhase.value = progressPhases[Math.min(Math.floor(step / 1.2), progressPhases.length - 1)]
  }, 800)
}

function stopProgressSimulation() {
  if (phaseTimer !== null) {
    clearInterval(phaseTimer)
    phaseTimer = null
  }
  progressPct.value = 100
  currentPhase.value = 'Concluído'
}

// ── API helpers ───────────────────────────────────────────────────────────────

async function fetchReadiness() {
  loadingReadiness.value = true
  readinessError.value = null
  try {
    const data = await $fetch<ReadinessResponse>(`${apiBase}/v1/ready`)
    readiness.value = data
  } catch (err: unknown) {
    readinessError.value = err instanceof Error ? err.message : 'Falha ao conectar ao serviço'
  } finally {
    loadingReadiness.value = false
  }
}

async function fetchCalibrationStatus() {
  try {
    const data = await $fetch<CalibrationResult>(`${apiBase}/v1/calibrate/status`)
    calibrationStatus.value = data
  } catch {
    // non-fatal — page still works without prior status
  }
}

async function runCalibration() {
  calibrating.value = true
  calibrationError.value = null
  calibrationDone.value = false
  startProgressSimulation()
  try {
    const result = await $fetch<CalibrationResult>(`${apiBase}/v1/calibrate`, { method: 'POST' })
    calibrationStatus.value = result
    calibrationDone.value = true
    // Refresh readiness after calibration
    await fetchReadiness()
  } catch (err: unknown) {
    calibrationError.value = err instanceof Error ? err.message : 'Calibração falhou'
  } finally {
    stopProgressSimulation()
    calibrating.value = false
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────

onMounted(async () => {
  await Promise.all([fetchReadiness(), fetchCalibrationStatus()])
})
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold">Admin / Configuração</h1>
    <p class="text-gray-500 text-sm">
      Operações manuais necessárias antes do modo Jogar estar totalmente funcional.
    </p>

    <!-- ── Service Readiness ──────────────────────────────────────────────── -->
    <section class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <h2 class="font-semibold text-gray-800">Disponibilidade do Serviço</h2>
        <button
          class="text-xs text-blue-600 hover:underline disabled:opacity-50"
          :disabled="loadingReadiness"
          @click="fetchReadiness"
        >
          {{ loadingReadiness ? 'Atualizando…' : 'Atualizar' }}
        </button>
      </div>

      <div class="px-5 py-4">
        <div v-if="readinessError" class="text-red-600 text-sm">{{ readinessError }}</div>

        <div v-else-if="!readiness" class="text-gray-400 text-sm animate-pulse">Carregando…</div>

        <div v-else class="space-y-2">
          <!-- Overall badge -->
          <div class="flex items-center gap-2 mb-3">
            <span
              class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium"
              :class="readiness.ok ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-700'"
            >
              <span class="w-2 h-2 rounded-full" :class="readiness.ok ? 'bg-green-500' : 'bg-red-500'" />
              {{ readiness.ok ? 'Todos os sistemas prontos' : 'Não pronto' }}
            </span>
            <span class="text-xs text-gray-400">v{{ readiness.version }}</span>
          </div>

          <!-- Per-check rows -->
          <div
            v-for="check in readiness.checks"
            :key="check.name"
            class="flex items-start gap-3 py-2 border-t border-gray-50"
          >
            <span class="mt-0.5 w-4 h-4 flex-shrink-0 flex items-center justify-center rounded-full text-xs"
              :class="check.ok ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'"
            >
              {{ check.ok ? '✓' : '✗' }}
            </span>
            <div class="min-w-0">
              <p class="text-sm font-medium capitalize text-gray-800">
                {{ check.name }}
                <span v-if="check.required" class="ml-1 text-xs text-gray-400">(obrigatório)</span>
              </p>
              <p class="text-xs text-gray-500 truncate">{{ check.detail }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Calibration ────────────────────────────────────────────────────── -->
    <section class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div class="px-5 py-4 border-b border-gray-100">
        <h2 class="font-semibold text-gray-800">Calibração do Motor de Previsão</h2>
        <p class="text-xs text-gray-500 mt-0.5">
          Deve ser executado pelo menos uma vez antes do modo Jogar estar disponível. Reexecute sempre que o conjunto de dados mudar ou após 14 dias.
        </p>
      </div>

      <div class="px-5 py-4 space-y-4">

        <!-- Current status -->
        <div v-if="calibrationStatus" class="flex flex-wrap gap-4 text-sm">
          <div>
            <p class="text-xs text-gray-400 uppercase tracking-wide">Estado</p>
            <span
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium mt-1"
              :class="calibrationStatus.ok ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'"
            >
              {{ calibrationStatus.ok ? 'Atualizado' : 'Desatualizado / não executado' }}
            </span>
          </div>
          <div v-if="calibrationStatus.last_calibrated_at">
            <p class="text-xs text-gray-400 uppercase tracking-wide">Última execução</p>
            <p class="mt-1 text-gray-700">{{ new Date(calibrationStatus.last_calibrated_at).toLocaleString() }}</p>
          </div>
          <div v-if="calibrationStatus.eval_metrics?.n_eval_rows">
            <p class="text-xs text-gray-400 uppercase tracking-wide">Linhas de avaliação</p>
            <p class="mt-1 text-gray-700">{{ calibrationStatus.eval_metrics.n_eval_rows }}</p>
          </div>
        </div>

        <!-- Eval metrics grid (shown after a run) -->
        <div
          v-if="calibrationStatus?.eval_metrics?.brier_score_calibrated != null"
          class="grid grid-cols-2 gap-3 text-sm"
        >
          <div class="bg-gray-50 rounded-lg px-4 py-3">
            <p class="text-xs text-gray-400">Brier score (bruto → calibrado)</p>
            <p class="font-mono font-medium text-gray-800 mt-1">
              {{ calibrationStatus!.eval_metrics!.brier_score_raw!.toFixed(4) }}
              →
              <span class="text-green-700">{{ calibrationStatus!.eval_metrics!.brier_score_calibrated!.toFixed(4) }}</span>
            </p>
          </div>
          <div class="bg-gray-50 rounded-lg px-4 py-3">
            <p class="text-xs text-gray-400">Log loss (bruto → calibrado)</p>
            <p class="font-mono font-medium text-gray-800 mt-1">
              {{ calibrationStatus!.eval_metrics!.log_loss_raw!.toFixed(4) }}
              →
              <span class="text-green-700">{{ calibrationStatus!.eval_metrics!.log_loss_calibrated!.toFixed(4) }}</span>
            </p>
          </div>
        </div>

        <!-- Progress bar (shown while running) -->
        <div v-if="calibrating" class="space-y-1.5">
          <div class="flex items-center justify-between text-xs text-gray-500">
            <span>{{ currentPhase }}</span>
            <span>{{ progressPct }}%</span>
          </div>
          <div class="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
            <div
              class="h-full bg-blue-500 rounded-full transition-all duration-700 ease-out"
              :style="{ width: `${progressPct}%` }"
            />
          </div>
        </div>

        <!-- Success banner -->
        <div v-if="calibrationDone && !calibrating" class="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-4 py-2">
          <span>✓</span> Calibração concluída — Modo Jogar agora está disponível.
        </div>

        <!-- Error -->
        <div v-if="calibrationError" class="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-4 py-2">
          {{ calibrationError }}
        </div>

        <!-- Run button -->
        <button
          class="px-5 py-2 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400"
          :class="calibrating
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-blue-600 text-white hover:bg-blue-700'"
          :disabled="calibrating"
          @click="runCalibration"
        >
          {{ calibrating ? 'Executando…' : (calibrationStatus?.ok ? 'Reexecutar Calibração' : 'Executar Calibração Agora') }}
        </button>
      </div>
    </section>

    <!-- ── Dataset Info ───────────────────────────────────────────────────── -->
    <section class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div class="px-5 py-4 border-b border-gray-100">
        <h2 class="font-semibold text-gray-800">Dataset</h2>
      </div>
      <div class="px-5 py-4 space-y-1 text-sm text-gray-600">
        <p>
          O conjunto de dados é lido de <code class="bg-gray-100 px-1 py-0.5 rounded text-xs">data.json</code> na raiz do repositório.
          É imutável — o serviço nunca escreve nele.
        </p>
        <p>
          Para atualizar o conjunto de dados, substitua <code class="bg-gray-100 px-1 py-0.5 rounded text-xs">data.json</code> e reinicie o serviço,
          em seguida reexecute a calibração acima.
        </p>
        <div v-if="readiness" class="mt-3">
          <template v-for="check in readiness.checks" :key="check.name">
            <div v-if="check.name === 'ingestion' && check.extra" class="text-xs text-gray-500 space-y-0.5 mt-1">
              <p v-for="(val, key) in check.extra" :key="key">
                <span class="font-medium capitalize">{{ String(key).replace(/_/g, ' ') }}:</span> {{ val }}
              </p>
            </div>
          </template>
        </div>
      </div>
    </section>
  </div>
</template>
