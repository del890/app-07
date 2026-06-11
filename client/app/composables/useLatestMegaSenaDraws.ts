import type { MegaSenaDraw } from '~/types/api'

const BASE = 'https://loteriascaixa-api.herokuapp.com'

export function useLatestMegaSenaDraws() {
  const draws = ref<MegaSenaDraw[]>([])
  const pending = ref(false)
  const error = ref<Error | null>(null)

  async function fetchDraws() {
    pending.value = true
    error.value = null
    try {
      const latest = await $fetch<MegaSenaDraw>(`${BASE}/api/megasena/latest`)
      const [prev1, prev2] = await Promise.all([
        $fetch<MegaSenaDraw>(`${BASE}/api/megasena/${latest.concurso - 1}`),
        $fetch<MegaSenaDraw>(`${BASE}/api/megasena/${latest.concurso - 2}`),
      ])
      draws.value = [latest, prev1, prev2].sort((a, b) => b.concurso - a.concurso)
    }
    catch (err) {
      error.value = err instanceof Error ? err : new Error('Falha ao carregar os sorteios da Mega Sena')
    }
    finally {
      pending.value = false
    }
  }

  fetchDraws()

  return { draws, pending, error, retry: fetchDraws }
}
