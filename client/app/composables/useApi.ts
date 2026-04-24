import type { ApiErrorEnvelope, DrawsPage, PredictionHistoryPage } from '~/types/api'

/**
 * Typed API client wrapping `$fetch` with canonical error-envelope handling.
 * Usage: const { get, post } = useApi()
 */
export function useApi() {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase as string

  async function get<T>(path: string, query?: Record<string, unknown>): Promise<T> {
    return $fetch<T>(`${baseURL}${path}`, {
      method: 'GET',
      params: query,
      onResponseError({ response }) {
        const body = response._data as ApiErrorEnvelope | undefined
        const msg = body?.error?.message ?? `HTTP ${response.status}`
        throw new Error(msg)
      },
    })
  }

  async function post<T>(path: string, body?: unknown): Promise<T> {
    return $fetch<T>(`${baseURL}${path}`, {
      method: 'POST',
      body,
      onResponseError({ response }) {
        const data = response._data as ApiErrorEnvelope | undefined
        const msg = data?.error?.message ?? `HTTP ${response.status}`
        throw new Error(msg)
      },
    })
  }

  function getDraws(page = 1, pageSize = 50): Promise<DrawsPage> {
    return get<DrawsPage>('/v1/dataset/draws', { page, page_size: pageSize })
  }

  function getPredictionHistory(
    kind?: 'next_draw' | 'scenario_path',
    page = 1,
    pageSize = 20,
  ): Promise<PredictionHistoryPage> {
    const query: Record<string, unknown> = { page, page_size: pageSize }
    if (kind) query.kind = kind
    return get<PredictionHistoryPage>('/v1/predictions/history', query)
  }

  return { get, post, getDraws, getPredictionHistory }
}
