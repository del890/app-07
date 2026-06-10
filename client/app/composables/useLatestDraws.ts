import type { LatestDraw } from '~/types/api'

const BASE = 'https://loteriascaixa-api.herokuapp.com'

export function useLatestDraws() {
  const draws = ref<LatestDraw[]>([])
  const pending = ref(false)
  const error = ref<Error | null>(null)

  async function fetchDraws() {
    pending.value = true
    error.value = null
    try {
      const latest = await $fetch<LatestDraw>(`${BASE}/api/lotofacil/latest`)
      const [prev1, prev2] = await Promise.all([
        $fetch<LatestDraw>(`${BASE}/api/lotofacil/${latest.concurso - 1}`),
        $fetch<LatestDraw>(`${BASE}/api/lotofacil/${latest.concurso - 2}`),
      ])
      draws.value = [latest, prev1, prev2].sort((a, b) => b.concurso - a.concurso)
    }
    catch (err) {
      error.value = err instanceof Error ? err : new Error('Falha ao carregar os sorteios')
    }
    finally {
      pending.value = false
    }
  }

  fetchDraws()

  return { draws, pending, error, retry: fetchDraws }
}
