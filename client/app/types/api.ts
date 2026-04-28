// API response types — keep in sync with service Pydantic models

// ── Errors ────────────────────────────────────────────────────────────────

export interface ApiErrorEnvelope {
  error: {
    code: string
    message: string
    details: Record<string, unknown>
  }
}

// ── Dataset / Provenance ──────────────────────────────────────────────────

export interface DatasetProvenance {
  total_draws: number
  first_date: string // ISO date
  last_date: string // ISO date
  source_path: string
  content_hash: string
}

// ── Statistics ────────────────────────────────────────────────────────────

export interface StatMeta {
  dataset_hash: string
  window: string // "full" | "last-N"
  window_size: number
  computed_at: string // ISO datetime
}

export interface NumberFrequency {
  number: number
  count: number
  share: number
}

export interface FrequencyResult {
  meta: StatMeta
  frequencies: NumberFrequency[]
}

export interface HotColdThreshold {
  hot_factor: number
  cold_factor: number
}

export interface GapEntry {
  number: number
  current_gap: number
  mean_gap: number
  max_gap: number
  classification: 'hot' | 'cold' | 'neutral'
}

export interface GapResult {
  meta: StatMeta
  threshold: HotColdThreshold
  gaps: GapEntry[]
}

export interface Combination {
  numbers: number[]
  count: number
}

export interface CooccurrenceResult {
  meta: StatMeta
  arity: number
  top_k: number
  combinations: Combination[]
}

export interface HistogramBin {
  value: number
  count: number
}

export interface StructuralResult {
  meta: StatMeta
  sum_min: number
  sum_max: number
  sum_histogram: HistogramBin[]
  even_count_histogram: HistogramBin[]
  quintile_histogram: HistogramBin[]
  quintile_per_draw_mean: number[]
  min_number_histogram: HistogramBin[]
  max_number_histogram: HistogramBin[]
}

export interface OrderResult {
  meta: StatMeta
  order_is_original: boolean
  label: string
}

export interface PiAlignmentResult {
  meta: StatMeta
  rule: string
  score: number
  explanation: string
}

// ── Correlations ──────────────────────────────────────────────────────────

export interface CorrelationResult {
  signal: string
  metric: string
  lag_draws: number
  alignment: string
  rho: number
  p_value: number
  q_value: number | null
  effect_size: number
  sample_size: number
  test_used: string
  under_powered: boolean
  significant: boolean
  artifact_type: 'research'
  disclaimer: string
}

// ── Predictions ───────────────────────────────────────────────────────────

export interface ModelVersion {
  name: string
  version: string
}

export interface PredictionProvenance {
  dataset_hash: string
  model_versions: ModelVersion[]
  agent_prompt_hash: string
  tool_trace: unknown[]
  computed_at: string // ISO datetime
}

export interface NextDrawPrediction {
  numbers: number[]
  confidence: number
  explanation: string
  calibrated: boolean
  provenance: PredictionProvenance
}

export interface ScenarioStep {
  step: number
  numbers: number[]
  confidence: number
  explanation: string
}

export interface ScenarioPathPrediction {
  horizon: number
  path: ScenarioStep[]
  calibrated: boolean
  provenance: PredictionProvenance
}

// ── SSE streaming events ──────────────────────────────────────────────────

export interface SseToolStartEvent {
  type: 'tool_start'
  tool_name: string
  tool_input: Record<string, unknown>
}

export interface SseToolResultEvent {
  type: 'tool_result'
  tool_name: string
  result: Record<string, unknown>
}

export interface SseFinalEvent {
  type: 'final'
  result: NextDrawPrediction | ScenarioPathPrediction
}

export type SseEvent = SseToolStartEvent | SseToolResultEvent | SseFinalEvent

// ── Historical draws ──────────────────────────────────────────────────────

export interface HistoricalDraw {
  index: number
  original_id: number
  date: string // ISO date
  numbers: number[]
}

export interface DrawsPage {
  total: number
  page: number
  page_size: number
  draws: HistoricalDraw[]
}

// ── Stored predictions ────────────────────────────────────────────────────

export interface StoredNextDraw {
  id: string
  kind: 'next_draw'
  stored_at: string // ISO datetime
  prediction: NextDrawPrediction
}

export interface StoredScenarioPath {
  id: string
  kind: 'scenario_path'
  stored_at: string // ISO datetime
  prediction: ScenarioPathPrediction
}

export type StoredPrediction = StoredNextDraw | StoredScenarioPath

export interface PredictionHistoryPage {
  total: number
  page: number
  page_size: number
  items: StoredPrediction[]
}

// ── Draw Profile ──────────────────────────────────────────────────────────

export interface DrawProfileRequest {
  numbers: number[]
}

export interface NumberProfile {
  number: number
  historical_count: number
  frequency_rank: number
}

export interface PairCooccurrence {
  numbers: [number, number]
  count: number
}

export interface DrawStructuralProfile {
  total_sum: number
  even_count: number
  odd_count: number
  min_number: number
  max_number: number
  range_span: number
  quintile_counts: number[] // length 5, counts per quintile 1–5, 6–10, 11–15, 16–20, 21–25
}

export interface DatasetMatch {
  original_id: number
  date: string
}

export interface DrawProfileResponse {
  numbers: number[]
  number_profiles: NumberProfile[]
  pair_cooccurrences: PairCooccurrence[]
  structural: DrawStructuralProfile
  dataset_match: DatasetMatch | null
}

// ── Local storage ─────────────────────────────────────────────────────────

export interface MyDrawEntry {
  id?: number       // auto-increment primary key (set by IndexedDB)
  savedAt: string   // ISO datetime
  numbers: number[]
  profile: DrawProfileResponse
}

// ── Ticket scanner ────────────────────────────────────────────────────────

export interface ScannedTicket {
  /** Up to 3 game sets; each is a sorted list of marked numbers (1–25). */
  games: number[][]
}

