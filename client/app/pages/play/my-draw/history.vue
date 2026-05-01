<script setup lang="ts">
import type { MyDrawEntry } from '~/types/api'
import { Button } from '~/components/ui/button'

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
  <div class="space-y-6">
    <div>
      <div class="flex items-center justify-between">
        <Button variant="ghost" as-child class="-ml-3">
          <NuxtLink to="/play/my-draw">← Meu Volante</NuxtLink>
        </Button>
        <Button
          v-if="entries.length"
          variant="ghost"
          size="sm"
          class="text-destructive hover:text-destructive"
          @click="handleClearAll"
        >
          Limpar tudo
        </Button>
      </div>
      <h1 class="text-2xl font-bold">Histórico do Meu Volante</h1>
    </div>

    <!-- Empty state -->
    <div v-if="!entries.length" class="text-center py-16">
      <p class="text-muted-foreground mb-4">Nenhuma análise salva.</p>
      <Button variant="ghost" as-child>
        <NuxtLink to="/play/my-draw">Analisar um sorteio →</NuxtLink>
      </Button>
    </div>

    <!-- Entry list -->
    <div v-else class="space-y-3 max-w-xl">
      <div
        v-for="entry in entries"
        :key="entry.id"
        class="bg-card border rounded-lg px-5 py-4"
      >
        <!-- Numbers -->
        <div class="flex flex-wrap gap-1.5 mb-2">
          <span
            v-for="n in entry.numbers.slice().sort((a, b) => a - b)"
            :key="n"
            class="w-8 h-8 flex items-center justify-center rounded-full bg-accent text-accent-foreground font-semibold text-xs"
          >
            {{ n }}
          </span>
        </div>

        <!-- Date + actions -->
        <div class="flex items-center justify-between mt-3">
          <span class="text-xs text-muted-foreground">{{ formatDate(entry.savedAt) }}</span>
          <div class="flex gap-2">
            <Button variant="ghost" size="sm" @click="handleLoad(entry)">Carregar</Button>
            <Button
              variant="ghost"
              size="sm"
              class="text-destructive hover:text-destructive"
              @click="handleDelete(entry.id!)"
            >
              Excluir
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
