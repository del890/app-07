import type { DrawProfileRequest, DrawProfileResponse } from '~/types/api'

export function useDrawProfile() {
  const { post } = useApi()
  const result = ref<DrawProfileResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchProfile(numbers: number[]): Promise<void> {
    loading.value = true
    error.value = null
    result.value = null
    try {
      const body: DrawProfileRequest = { numbers }
      result.value = await post<DrawProfileResponse>('/v1/statistics/draw-profile', body)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
    } finally {
      loading.value = false
    }
  }

  return { result, loading, error, fetchProfile }
}
