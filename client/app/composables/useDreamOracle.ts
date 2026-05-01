import type { DreamOracleResult } from '~/types/api'

export type DreamOracleStatus = 'idle' | 'streaming' | 'done' | 'error'

interface SseOracleEvent {
  type: string
  [key: string]: unknown
}

/**
 * Composable for the dream-oracle SSE endpoint.
 */
export function useDreamOracle() {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase as string

  const status = ref<DreamOracleStatus>('idle')
  const events = ref<SseOracleEvent[]>([])
  const result = ref<DreamOracleResult | null>(null)
  const error = ref<string | null>(null)

  function reset() {
    status.value = 'idle'
    events.value = []
    result.value = null
    error.value = null
  }

  async function interpretDream(body: { description: string }): Promise<void> {
    await _streamPost('/v1/oracle/dream', body)
  }

  async function _streamPost(path: string, body: unknown): Promise<void> {
    reset()
    status.value = 'streaming'

    try {
      const response = await fetch(`${baseURL}${path}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
        },
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        const msg =
          (data as { error?: { message?: string } })?.error?.message ??
          `HTTP ${response.status}`
        throw new Error(msg)
      }

      const contentType = response.headers.get('content-type') ?? ''

      if (contentType.includes('text/event-stream') && response.body) {
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
              const event = JSON.parse(json) as SseOracleEvent
              events.value.push(event)
              if (event.type === 'final' && event.result) {
                result.value = event.result as DreamOracleResult
              }
            } catch {
              // Ignore malformed SSE frames
            }
          }
        }
      } else {
        const data = await response.json()
        result.value = data as DreamOracleResult
      }

      status.value = 'done'
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err)
      status.value = 'error'
    }
  }

  return { status, events, result, error, interpretDream, reset }
}
