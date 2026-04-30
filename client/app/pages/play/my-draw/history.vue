<script setup lang="ts">
import type { MyDrawEntry } from '~/types/api'

// State shared via useState so the my-draw index page can pre-fill from here
const preloadNumbers = useState<number[] | null>('my-draw.preload', () => null)

const { listEntries, deleteEntry, clearEntries } = useMyDrawStore()
const entries = ref<MyDrawEntry[]>([])
const router = useRouter()

onMounted(async () => {
  entries.value = await listEntries()
})

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function handleDelete(id: number): Promise<void> {
  await deleteEntry(id)
  entries.value = entries.value.filter((e) => e.id !== id)
}

async function handleClearAll(): Promise<void> {
  if (!window.confirm('Apagar todas as análises? Esta ação não pode ser desfeita.')) return
  await clearEntries()
  entries.value = []
}

function handleLoad(entry: MyDrawEntry): void {
  preloadNumbers.value = [...entry.numbers]
  router.push('/play/my-draw')
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <NuxtLink to="/play/my-draw" class="text-sm text-blue-600 hover:underline">← Meu Volante</NuxtLink>
      <button
        v-if="entries.length"
        type="button"
        class="text-xs text-red-400 hover:text-red-600"
        @click="handleClearAll"
      >
        Limpar tudo
      </button>
    </div>

    <h1 class="text-2xl font-bold mb-6">Histórico do Meu Volante</h1>

    <!-- Empty state -->
    <div v-if="!entries.length" class="text-center py-16">
      <p class="text-gray-400 mb-4">Nenhuma análise salva.</p>
      <NuxtLink to="/play/my-draw" class="text-sm text-purple-600 hover:underline">
        Analisar um sorteio →
      </NuxtLink>
    </div>

    <!-- Entry list -->
    <div v-else class="space-y-3 max-w-xl">
      <div
        v-for="entry in entries"
        :key="entry.id"
        class="bg-white border border-gray-200 rounded-lg px-5 py-4"
      >
        <!-- Numbers -->
        <div class="flex flex-wrap gap-1.5 mb-2">
          <span
            v-for="n in entry.numbers.slice().sort((a, b) => a - b)"
            :key="n"
            class="w-8 h-8 flex items-center justify-center rounded-full bg-purple-100 text-purple-800 font-semibold text-xs"
          >
            {{ n }}
          </span>
        </div>

        <!-- Date + actions -->
        <div class="flex items-center justify-between mt-3">
          <span class="text-xs text-gray-400">{{ formatDate(entry.savedAt) }}</span>
          <div class="flex gap-4">
            <button
              type="button"
              class="text-xs text-purple-600 hover:text-purple-800 font-medium"
              @click="handleLoad(entry)"
            >
              Carregar
            </button>
            <button
              type="button"
              class="text-xs text-red-400 hover:text-red-600"
              @click="handleDelete(entry.id!)"
            >
              Excluir
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
