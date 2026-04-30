import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, computed, onMounted } from 'vue'

// ──────────────────────────────────────────────────────────────────────────────
// Stubs for Nuxt auto-imports not available in Vitest
// ──────────────────────────────────────────────────────────────────────────────

// Stub $fetch used by useApi
const mockFetch = vi.fn()
vi.stubGlobal('$fetch', mockFetch)

// Minimal stubs for Nuxt composables
vi.stubGlobal('useRuntimeConfig', () => ({
  public: { apiBase: 'http://localhost:8000' },
}))
vi.stubGlobal('useState', <T>(_key: string, init?: () => T) => ref<T>(init?.() as T))
vi.stubGlobal('readonly', (v: unknown) => v)

// Forward Nuxt auto-imported Vue primitives to the real Vue implementation
vi.stubGlobal('ref', ref)
vi.stubGlobal('computed', computed)
vi.stubGlobal('onMounted', onMounted)

// ──────────────────────────────────────────────────────────────────────────────
// useApi
// ──────────────────────────────────────────────────────────────────────────────

const { useApi } = await import('../app/composables/useApi')

describe('useApi', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('get() calls $fetch with the correct url and method', async () => {
    mockFetch.mockResolvedValue({ total_draws: 100 })
    const { get } = useApi()
    const result = await get('/v1/dataset')
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/v1/dataset',
      expect.objectContaining({ method: 'GET' }),
    )
    expect(result).toEqual({ total_draws: 100 })
  })

  it('post() calls $fetch with method POST and body', async () => {
    mockFetch.mockResolvedValue({ rho: 0.1 })
    const { post } = useApi()
    const body = { signal: 'sp500', metric: 'frequency', lag_draws: 0 }
    await post('/v1/correlations', body)
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/v1/correlations',
      expect.objectContaining({ method: 'POST', body }),
    )
  })

  it('get() surfaces the error envelope message on failure', async () => {
    mockFetch.mockImplementation((_url: string, opts: { onResponseError?: (ctx: unknown) => void }) => {
      opts?.onResponseError?.({
        response: {
          status: 404,
          _data: { error: { message: 'not found', code: 'not_found', details: {} } },
        },
      })
      return Promise.reject(new Error('not found'))
    })
    const { get } = useApi()
    await expect(get('/v1/does-not-exist')).rejects.toThrow()
  })
})

// ──────────────────────────────────────────────────────────────────────────────
// ConfidenceBadge — uses real Vue reactivity (no ref/computed stubs needed)
// ──────────────────────────────────────────────────────────────────────────────

import ConfidenceBadge from '../app/components/ConfidenceBadge.vue'

describe('ConfidenceBadge', () => {
  it('renders percentage for valid confidence', () => {
    const w = mount(ConfidenceBadge, { props: { confidence: 0.72 } })
    expect(w.text()).toContain('72%')
  })

  it('renders nothing for confidence >= 1.0', () => {
    const w = mount(ConfidenceBadge, { props: { confidence: 1.0 } })
    expect(w.text()).toBe('')
  })

  it('renders nothing for confidence <= 0', () => {
    const w = mount(ConfidenceBadge, { props: { confidence: 0 } })
    expect(w.text()).toBe('')
  })

  it('renders nothing when confidence is null', () => {
    const w = mount(ConfidenceBadge, { props: { confidence: null } })
    expect(w.text()).toBe('')
  })

  it('renders nothing when confidence is undefined', () => {
    const w = mount(ConfidenceBadge, { props: { confidence: undefined } })
    expect(w.text()).toBe('')
  })

  it('applies green class for high confidence', () => {
    const w = mount(ConfidenceBadge, { props: { confidence: 0.8 } })
    expect(w.html()).toContain('bg-green-100')
  })

  it('applies yellow class for medium confidence', () => {
    const w = mount(ConfidenceBadge, { props: { confidence: 0.5 } })
    expect(w.html()).toContain('bg-yellow-100')
  })

  it('applies red class for low confidence', () => {
    const w = mount(ConfidenceBadge, { props: { confidence: 0.2 } })
    expect(w.html()).toContain('bg-red-100')
  })
})

// ──────────────────────────────────────────────────────────────────────────────
// useSsePrediction — unit-level logic without real network
// ──────────────────────────────────────────────────────────────────────────────

describe('useSsePrediction — initial state', () => {
  it('starts in idle state', async () => {
    vi.stubGlobal('fetch', vi.fn())
    const { useSsePrediction } = await import('../app/composables/useSsePrediction')
    const { status, result, error, events } = useSsePrediction()
    expect(status.value).toBe('idle')
    expect(result.value).toBeNull()
    expect(error.value).toBeNull()
    expect(events.value).toEqual([])
  })
})

describe('useSsePrediction — error handling', () => {
  it('sets status=error when fetch rejects', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network failure')))
    const { useSsePrediction } = await import('../app/composables/useSsePrediction')
    const pred = useSsePrediction()
    await pred.predictNextDraw()
    expect(pred.status.value).toBe('error')
    expect(pred.error.value).toBe('network failure')
  })
})

// ──────────────────────────────────────────────────────────────────────────────
// usePredictionExplanation
// ──────────────────────────────────────────────────────────────────────────────

describe('normalizePredictionExplanation', () => {
  it('keeps plain text explanations as summary', async () => {
    const { normalizePredictionExplanation } = await import('../app/composables/usePredictionExplanation')
    const result = normalizePredictionExplanation('Analise com base nos ultimos sorteios.')

    expect(result.summary).toBe('Analise com base nos ultimos sorteios.')
    expect(result.isStructured).toBe(false)
    expect(result.highlightSections).toEqual([])
    expect(result.topProbabilities).toEqual([])
  })

  it('parses structured JSON explanation strings', async () => {
    const { normalizePredictionExplanation } = await import('../app/composables/usePredictionExplanation')
    const payload = JSON.stringify({
      summary: 'Resumo principal',
      top_probabilities: [
        { number: 10, probability: 0.7 },
        { number: 20, probability: 0.66 },
      ],
      frequency_full_highlights: {
        top_numbers_by_share: [{ number: 10, share: 0.62 }],
        note: 'Numero 10 lidera historicamente.',
      },
      provenance_anchor: {
        record_count: 3656,
        date_range: '2003-09-29 to 2026-04-08',
        dataset_hash: 'abc123abc123abc123',
      },
    })

    const result = normalizePredictionExplanation(payload)

    expect(result.summary).toBe('Resumo principal')
    expect(result.isStructured).toBe(true)
    expect(result.topProbabilities).toHaveLength(2)
    expect(result.highlightSections).toHaveLength(1)
    expect(result.provenance).toHaveLength(3)
  })

  it('supports object-shaped explanation input', async () => {
    const { normalizePredictionExplanation } = await import('../app/composables/usePredictionExplanation')
    const result = normalizePredictionExplanation({
      summary: 'Resumo vindo como objeto',
      top_probabilities: [{ number: 13, probability: 0.63 }],
    })

    expect(result.summary).toBe('Resumo vindo como objeto')
    expect(result.isStructured).toBe(true)
    expect(result.topProbabilities[0]?.number).toBe(13)
  })

  it('falls back safely for malformed JSON-like strings', async () => {
    const { normalizePredictionExplanation } = await import('../app/composables/usePredictionExplanation')
    const malformed = '{"summary": "foo", invalid}'
    const result = normalizePredictionExplanation(malformed)

    expect(result.isStructured).toBe(false)
    expect(result.fallbackText).toBe(malformed)
    expect(result.summary).toContain('Resumo analitico indisponivel')
  })
})
