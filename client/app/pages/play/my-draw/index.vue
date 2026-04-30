<script setup lang="ts">
import type { DrawProfileResponse, MyDrawEntry } from '~/types/api'

// Pre-fill numbers when navigated from history page
const preloadNumbers = useState<number[] | null>('my-draw.preload', () => null)

const selectedNumbers = ref<number[]>(preloadNumbers.value ?? [])
preloadNumbers.value = null // consume once

const { result, loading, error, fetchProfile } = useDrawProfile()
const { saveEntry, listEntries, storeAvailable } = useMyDrawStore()

const profile = computed(() => result.value as DrawProfileResponse | null)
const isReady = computed(() => selectedNumbers.value.length === 15)

// Build a quick-lookup map: number → NumberProfile
const profileByNumber = computed(() => {
  const map = new Map<number, { historical_count: number; frequency_rank: number }>()
  profile.value?.number_profiles.forEach((p) => map.set(p.number, p))
  return map
})

const top5Pairs = computed(() => profile.value?.pair_cooccurrences.slice(0, 5) ?? [])

const quintileLabels = ['1–5', '6–10', '11–15', '16–20', '21–25']

// Recent history (latest 5)
const recentEntries = ref<MyDrawEntry[]>([])

async function refreshRecent(): Promise<void> {
  const all = await listEntries()
  recentEntries.value = all.slice(0, 5)
}

onMounted(refreshRecent)

async function submit(): Promise<void> {
  if (!isReady.value) return
  await fetchProfile(selectedNumbers.value)
}

// Auto-save after successful analysis (fire-and-forget)
watch(
  () => result.value,
  async (newResult) => {
    if (!newResult) return
    saveEntry({ numbers: selectedNumbers.value, profile: newResult as DrawProfileResponse }).catch(
      () => {},
    )
    await refreshRecent()
  },
)

function loadEntry(entry: MyDrawEntry): void {
  selectedNumbers.value = [...entry.numbers]
  result.value = null
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <NuxtLink to="/play" class="text-sm text-blue-600 hover:underline">← Jogar</NuxtLink>
      <NuxtLink
        to="/play/my-draw/history"
        class="text-sm text-gray-500 hover:text-gray-700 hover:underline"
      >
        Ver histórico →
      </NuxtLink>
    </div>
    <h1 class="text-2xl font-bold mb-2">Meu Volante</h1>
    <p class="text-sm text-gray-500 mb-4">
      Selecione 15 números para ver insights estatísticos e verificar se essa combinação já apareceu antes.
    </p>

    <!-- Import from scan shortcut -->
    <div class="mb-6">
      <NuxtLink
        to="/play/scan"
        class="inline-flex items-center gap-2 px-4 py-2 bg-teal-50 border border-teal-200 text-teal-700 text-sm font-medium rounded-lg hover:bg-teal-100 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        Importar do escaneamento
      </NuxtLink>
    </div>

    <!-- Selector -->
    <div class="bg-white border border-gray-200 rounded-lg p-5 max-w-sm mb-4">
      <DrawSelector v-model="selectedNumbers" />
    </div>

    <!-- Submit -->
    <button
      type="button"
      class="px-6 py-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      :disabled="!isReady || loading"
      @click="submit"
    >
      {{ loading ? 'Analisando…' : 'Analisar Seleção' }}
    </button>

    <!-- Error -->
    <div v-if="error" class="mt-4 text-red-600 text-sm">{{ error }}</div>

    <!-- Result panel -->
    <div v-if="profile" class="mt-8 space-y-6 max-w-xl">
      <!-- Dataset match banner -->
      <div
        v-if="profile.dataset_match"
        class="bg-amber-50 border border-amber-300 rounded-lg px-5 py-4"
      >
        <p class="text-sm font-semibold text-amber-800">
          Este sorteio foi realizado em {{ profile.dataset_match.date }} (sorteio
          #{{ profile.dataset_match.original_id }}).
        </p>
      </div>
      <div v-else class="bg-green-50 border border-green-200 rounded-lg px-5 py-4">
        <p class="text-sm text-green-800">Esta combinação nunca foi sorteada antes.</p>
      </div>

      <!-- Numbers with frequency indicators -->
      <div class="bg-white border border-gray-200 rounded-lg p-5">
        <h2 class="font-semibold text-gray-800 mb-4">Frequências por Número</h2>
        <div class="grid grid-cols-5 gap-3">
          <div
            v-for="n in profile.numbers.slice().sort((a, b) => a - b)"
            :key="n"
            class="flex flex-col items-center"
          >
            <span
              class="w-11 h-11 flex items-center justify-center rounded-full bg-purple-600 text-white font-bold text-sm mb-1"
            >
              {{ n }}
            </span>
            <span
              v-if="profileByNumber.get(n)"
              class="text-xs text-gray-500"
              :title="`Sorteado ${profileByNumber.get(n)!.historical_count} vezes`"
            >
              {{ profileByNumber.get(n)!.historical_count }}×
            </span>
            <span
              v-if="profileByNumber.get(n)"
              class="text-xs text-gray-400"
              :title="`Posição de frequência`"
            >
              #{{ profileByNumber.get(n)!.frequency_rank }}
            </span>
          </div>
        </div>
      </div>

      <!-- Top co-occurring pairs -->
      <div v-if="top5Pairs.length" class="bg-white border border-gray-200 rounded-lg p-5">
        <h2 class="font-semibold text-gray-800 mb-4">Pares com Maior Co-ocorrência</h2>
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-gray-500 border-b border-gray-100">
              <th class="pb-2 font-medium">Par</th>
              <th class="pb-2 font-medium text-right">Vezes juntos</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(pair, i) in top5Pairs"
              :key="i"
              class="border-b border-gray-50 last:border-0"
            >
              <td class="py-2 font-mono">{{ pair.numbers[0] }} &amp; {{ pair.numbers[1] }}</td>
              <td class="py-2 text-right text-gray-600">{{ pair.count }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Structural summary -->
      <div class="bg-white border border-gray-200 rounded-lg p-5">
        <h2 class="font-semibold text-gray-800 mb-4">Perfil Estrutural</h2>
        <dl class="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
          <div>
            <dt class="text-gray-500">Soma</dt>
            <dd class="font-semibold text-gray-800">{{ profile.structural.total_sum }}</dd>
          </div>
          <div>
            <dt class="text-gray-500">Intervalo</dt>
            <dd class="font-semibold text-gray-800">
              {{ profile.structural.min_number }}–{{ profile.structural.max_number }} (amplitude
              {{ profile.structural.range_span }})
            </dd>
          </div>
          <div>
            <dt class="text-gray-500">Par / Ímpar</dt>
            <dd class="font-semibold text-gray-800">
              {{ profile.structural.even_count }} pares · {{ profile.structural.odd_count }} ímpares
            </dd>
          </div>
        </dl>

        <!-- Quintile distribution -->
        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-2">Distribuição por quintil</p>
          <div class="flex gap-2">
            <div
              v-for="(count, idx) in profile.structural.quintile_counts"
              :key="idx"
              class="flex-1 flex flex-col items-center"
            >
              <div class="w-full bg-gray-100 rounded-sm overflow-hidden h-10 flex items-end">
                <div
                  class="w-full bg-purple-400 rounded-sm transition-all"
                  :style="{ height: `${(count / 15) * 100}%` }"
                />
              </div>
              <span class="text-xs text-gray-500 mt-1">{{ quintileLabels[idx] }}</span>
              <span class="text-xs font-semibold text-gray-700">{{ count }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent analyses panel -->
    <div v-if="storeAvailable && recentEntries.length" class="mt-10 max-w-xl">
      <h2 class="font-semibold text-gray-700 mb-3 text-sm uppercase tracking-wide">
        Análises recentes
      </h2>
      <div class="space-y-2">
        <div
          v-for="entry in recentEntries"
          :key="entry.id"
          class="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-4 py-3"
        >
          <div>
            <p class="font-mono text-xs text-gray-600">
              {{ entry.numbers.slice().sort((a, b) => a - b).join(', ') }}
            </p>
            <p class="text-xs text-gray-400 mt-0.5">{{ formatDate(entry.savedAt) }}</p>
          </div>
          <button
            type="button"
            class="text-xs text-purple-600 hover:text-purple-800 font-medium ml-4 shrink-0"
            @click="loadEntry(entry)"
          >
            Carregar
          </button>
        </div>
      </div>
      <NuxtLink
        to="/play/my-draw/history"
        class="mt-3 inline-block text-xs text-gray-400 hover:text-gray-600 hover:underline"
      >
        Ver histórico completo →
      </NuxtLink>
    </div>
  </div>
</template>
