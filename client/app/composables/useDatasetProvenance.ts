import type { DatasetProvenance } from '~/types/api'

/** Globally cached dataset provenance. */
const _provenance = useState<DatasetProvenance | null>('dataset.provenance', () => null)
const _loaded = useState<boolean>('dataset.loaded', () => false)
const _error = useState<string | null>('dataset.error', () => null)

export function useDatasetProvenance() {
  const { get } = useApi()

  async function load(): Promise<void> {
    if (_loaded.value) return
    try {
      _provenance.value = await get<DatasetProvenance>('/v1/dataset')
      _loaded.value = true
      _error.value = null
    } catch (err) {
      _error.value = err instanceof Error ? err.message : 'Failed to load dataset provenance'
    }
  }

  return {
    provenance: readonly(_provenance),
    loaded: readonly(_loaded),
    error: readonly(_error),
    load,
  }
}
