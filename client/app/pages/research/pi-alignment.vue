<script setup lang="ts">
import type { PiAlignmentResult } from '~/types/api'

const { get } = useApi()

const rules = ['digit_sum_mod10', 'position_digit_match']
const selectedRule = ref(rules[0])
const targetIndex = ref<number | null>(null)
const targetInput = ref('')

const { data, pending, error, refresh } = await useAsyncData<PiAlignmentResult>(
  'pi-alignment',
  () =>
    get('/v1/statistics/pi-alignment', {
      rule: selectedRule.value,
      ...(targetIndex.value !== null ? { target: targetIndex.value } : {}),
    }),
  { watch: [selectedRule, targetIndex] },
)

function applyTarget() {
  const n = parseInt(targetInput.value)
  targetIndex.value = Number.isFinite(n) && n >= 0 ? n : null
}
</script>

<template>
  <div>
    <NuxtLink to="/research" class="text-sm text-blue-600 hover:underline mb-4 block">← Pesquisa</NuxtLink>
    <h1 class="text-2xl font-bold mb-4">Análise de Alinhamento PI</h1>

    <div class="flex flex-wrap items-center gap-4 mb-6 text-sm">
      <label class="flex items-center gap-2">
        Regra
        <select v-model="selectedRule" class="border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-400">
          <option v-for="r in rules" :key="r" :value="r">{{ r }}</option>
        </select>
      </label>
      <label class="flex items-center gap-2">
        Índice alvo
        <input
          v-model="targetInput"
          type="number"
          min="0"
          placeholder="(sorteio mais recente)"
          class="border rounded px-2 py-1 w-36 focus:outline-none focus:ring-2 focus:ring-blue-400"
          @keydown.enter="applyTarget"
        />
        <button class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700" @click="applyTarget">Aplicar</button>
      </label>
    </div>

    <div v-if="pending" class="text-gray-400 py-8 text-center">Carregando…</div>
    <div v-else-if="error" class="text-red-600 py-4">{{ error.message }}</div>
    <div v-else-if="data" class="bg-white rounded-lg border border-gray-200 p-6 max-w-2xl">
      <div class="flex items-center gap-3 mb-3">
        <span class="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">{{ data.rule }}</span>
        <span class="text-2xl font-bold tabular-nums">{{ data.score.toFixed(4) }}</span>
        <span class="text-xs text-gray-500">pontuação de alinhamento</span>
      </div>
      <p class="text-gray-700 text-sm">{{ data.explanation }}</p>
    </div>
  </div>
</template>
