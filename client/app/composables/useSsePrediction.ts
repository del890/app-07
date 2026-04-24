import type { NextDrawPrediction, ScenarioPathPrediction, SseEvent } from '~/types/api'

export type PredictionStatus = 'idle' | 'streaming' | 'done' | 'error'

/**
 * Composable for streaming prediction endpoints via SSE.
 * Falls back to plain JSON if EventSource connection fails or the backend
 * returns non-streaming content.
 */
export function useSsePrediction() {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase as string

  const status = ref<PredictionStatus>('idle')
  const events = ref<SseEvent[]>([])
  const result = ref<NextDrawPrediction | ScenarioPathPrediction | null>(null)
  const error = ref<string | null>(null)

  function reset() {
    status.value = 'idle'
    events.value = []
    result.value = null
    error.value = null
  }

  async function predictNextDraw(body: {
    baseline_weight?: number
    learned_weight?: number
    model?: string
  } = {}): Promise<void> {
    await _streamPost('/v1/predictions/next-draw', body)
  }

  async function predictScenarioPath(body: {
    horizon?: number
    model?: string
  } = {}): Promise<void> {
    await _streamPost('/v1/predictions/scenario-path', body)
  }

  async function _streamPost(path: string, body: unknown): Promise<void> {
    reset()
    status.value = 'streaming'

    try {
      // Attempt SSE streaming first
      const response = await fetch(`${baseURL}${path}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        const msg = (data as { error?: { message?: string } })?.error?.message ?? `HTTP ${response.status}`
        throw new Error(msg)
      }

      const contentType = response.headers.get('content-type') ?? ''

      if (contentType.includes('text/event-stream') && response.body) {
        // Parse SSE stream
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })

          const lines = buffer.split('\n\n')
          buffer = lines.pop() ?? ''

          for (const chunk of lines) {
            const dataLine = chunk.split('\n').find((l) => l.startsWith('data: '))
            if (!dataLine) continue
            const json = dataLine.slice(6)
            try {
              const event = JSON.parse(json) as SseEvent
              events.value.push(event)
              if (event.type === 'final') {
                result.value = event.result
              }
            } catch {
              // Ignore malformed SSE frames
            }
          }
        }
      } else {
        // JSON fallback
        const data = await response.json()
        result.value = data as NextDrawPrediction | ScenarioPathPrediction
      }

      status.value = 'done'
    } catch (err) {
      status.value = 'error'
      error.value = err instanceof Error ? err.message : 'Prediction failed'
    }
  }

  return {
    status: readonly(status),
    events: readonly(events),
    result: readonly(result),
    error: readonly(error),
    predictNextDraw,
    predictScenarioPath,
    reset,
  }
}
