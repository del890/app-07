type UnknownRecord = Record<string, unknown>

export interface ExplanationProbability {
  number: number
  probability: number
}

export interface ExplanationHighlightSection {
  key: string
  title: string
  items: string[]
  note?: string
}

export interface NormalizedPredictionExplanation {
  summary: string
  highlightSections: ExplanationHighlightSection[]
  topProbabilities: ExplanationProbability[]
  provenance: string[]
  fallbackText?: string
  isStructured: boolean
}

const FALLBACK_SUMMARY = 'Resumo analitico indisponivel. Exibindo detalhes brutos recebidos.'

const FIELD_LABELS: Record<string, string> = {
  frequency_full_highlights: 'Frequencia historica completa',
  frequency_rolling_100_highlights: 'Frequencia nos ultimos 100 sorteios',
  gap_statistics_highlights: 'Lacunas e numeros quentes/frios',
  structural_distribution_highlights: 'Distribuicao estrutural',
  cooccurrence_highlights: 'Coocorrencias relevantes',
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function toSafeString(value: unknown): string {
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return ''
}

function looksLikeStructuredInput(value: string): boolean {
  const trimmed = value.trim()
  return trimmed.startsWith('{') || trimmed.startsWith('[')
}

function humanizeKey(key: string): string {
  if (FIELD_LABELS[key]) return FIELD_LABELS[key]
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatProbabilityValue(probability: number): string {
  return `${Math.round(probability * 100)}%`
}

function formatObjectForBullet(entry: UnknownRecord): string {
  const rawNumber = entry.number
  const rawShare = entry.share
  const rawProbability = entry.probability
  const rawCount = entry.count
  const rawPair = entry.pair

  if (typeof rawNumber === 'number' && typeof rawProbability === 'number') {
    return `Numero ${rawNumber}: ${formatProbabilityValue(rawProbability)}`
  }
  if (typeof rawNumber === 'number' && typeof rawShare === 'number') {
    return `Numero ${rawNumber}: presenca ${(rawShare * 100).toFixed(1)}%`
  }
  if (Array.isArray(rawPair) && rawPair.length === 2 && typeof rawCount === 'number') {
    return `Par ${rawPair[0]}-${rawPair[1]}: ${rawCount} ocorrencias`
  }
  if (typeof rawCount === 'number') {
    const label = Object.entries(entry)
      .filter(([k]) => k !== 'count')
      .map(([k, v]) => `${humanizeKey(k)}: ${toSafeString(v)}`)
      .filter(Boolean)
      .join(', ')
    return label ? `${label} (${rawCount})` : `${rawCount}`
  }

  const compact = Object.entries(entry)
    .map(([k, v]) => `${humanizeKey(k)}: ${toSafeString(v)}`)
    .filter((line) => !line.endsWith(': '))
    .join(' | ')
  return compact || JSON.stringify(entry)
}

function toBulletList(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  return value
    .map((item) => {
      if (isRecord(item)) return formatObjectForBullet(item)
      return toSafeString(item)
    })
    .filter(Boolean)
    .slice(0, 6)
}

function extractTopProbabilities(source: UnknownRecord): ExplanationProbability[] {
  const rawTop = source.top_probabilities
  if (!Array.isArray(rawTop)) return []

  return rawTop
    .map((item) => {
      if (!isRecord(item)) return null
      const number = item.number
      const probability = item.probability
      if (typeof number !== 'number' || typeof probability !== 'number') return null
      return { number, probability }
    })
    .filter((item): item is ExplanationProbability => item !== null)
    .slice(0, 5)
}

function extractHighlights(source: UnknownRecord): ExplanationHighlightSection[] {
  const sections: ExplanationHighlightSection[] = []

  for (const [key, value] of Object.entries(source)) {
    if (!key.endsWith('_highlights') || !isRecord(value)) continue

    const note = toSafeString(value.note)
    const items = Object.entries(value)
      .filter(([innerKey]) => innerKey !== 'note')
      .flatMap(([, innerValue]) => toBulletList(innerValue))

    if (items.length === 0 && !note) continue

    sections.push({
      key,
      title: humanizeKey(key),
      items,
      note: note || undefined,
    })
  }

  return sections
}

function extractProvenance(source: UnknownRecord): string[] {
  const anchor = source.provenance_anchor
  if (!isRecord(anchor)) return []

  const lines: string[] = []
  if (typeof anchor.record_count === 'number') {
    lines.push(`${anchor.record_count} sorteios analisados`)
  }
  const dateRange = toSafeString(anchor.date_range)
  if (dateRange) lines.push(`Janela: ${dateRange}`)
  const datasetHash = toSafeString(anchor.dataset_hash)
  if (datasetHash) lines.push(`Dataset: ${datasetHash.slice(0, 12)}`)
  return lines
}

function fromStructuredObject(source: UnknownRecord, originalInput: unknown): NormalizedPredictionExplanation {
  const summary = toSafeString(source.summary)
  const highlightSections = extractHighlights(source)
  const topProbabilities = extractTopProbabilities(source)
  const provenance = extractProvenance(source)

  const hasStructuredContent = summary.length > 0 || highlightSections.length > 0 || topProbabilities.length > 0
  if (!hasStructuredContent) {
    const fallbackText = typeof originalInput === 'string' ? originalInput.trim() : JSON.stringify(source)
    return {
      summary: FALLBACK_SUMMARY,
      highlightSections: [],
      topProbabilities: [],
      provenance: [],
      fallbackText,
      isStructured: false,
    }
  }

  return {
    summary: summary || 'Analise estruturada recebida com sucesso.',
    highlightSections,
    topProbabilities,
    provenance,
    isStructured: true,
  }
}

export function normalizePredictionExplanation(input: unknown): NormalizedPredictionExplanation {
  if (isRecord(input)) {
    return fromStructuredObject(input, input)
  }

  const textInput = toSafeString(input).trim()
  if (!textInput) {
    return {
      summary: 'Sem explicacao disponivel para esta sugestao.',
      highlightSections: [],
      topProbabilities: [],
      provenance: [],
      isStructured: false,
    }
  }

  if (!looksLikeStructuredInput(textInput)) {
    return {
      summary: textInput,
      highlightSections: [],
      topProbabilities: [],
      provenance: [],
      isStructured: false,
    }
  }

  try {
    const parsed = JSON.parse(textInput) as unknown
    if (isRecord(parsed)) {
      return fromStructuredObject(parsed, textInput)
    }
    return {
      summary: FALLBACK_SUMMARY,
      highlightSections: [],
      topProbabilities: [],
      provenance: [],
      fallbackText: textInput,
      isStructured: false,
    }
  } catch {
    return {
      summary: FALLBACK_SUMMARY,
      highlightSections: [],
      topProbabilities: [],
      provenance: [],
      fallbackText: textInput,
      isStructured: false,
    }
  }
}