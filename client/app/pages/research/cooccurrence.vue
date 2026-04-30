<script setup lang="ts">
import type { CooccurrenceResult } from '~/types/api'

const { get } = useApi()

const arity = ref(2)
const topK = ref(10)

const { data, pending, error } = await useAsyncData<CooccurrenceResult>(
  'cooccurrence',
  () => get('/v1/statistics/cooccurrence', { arity: arity.value, top_k: topK.value }),
  { watch: [arity, topK] },
)
</script>

<template>
  <div>
    <NuxtLink to="/research" class="text-sm text-blue-600 hover:underline mb-4 block">← Pesquisa</NuxtLink>
    <h1 class="text-2xl font-bold mb-4">Explorador de Co-ocorrência</h1>

    <div class="flex flex-wrap items-center gap-4 mb-6 text-sm">
      <label class="flex items-center gap-2">
        Arity
        <select v-model.number="arity" class="border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-400">
          <option :value="2">Pares (2)</option>
          <option :value="3">Trios (3)</option>
          <option :value="4">Quádruplos (4)</option>
        </select>
      </label>
      <label class="flex items-center gap-2">
        Top K
        <input v-model.number="topK" type="number" min="1" max="500"
          class="border rounded px-2 py-1 w-20 focus:outline-none focus:ring-2 focus:ring-blue-400" />
      </label>
    </div>

    <div v-if="pending" class="text-gray-400 py-8 text-center">Carregando…</div>
    <div v-else-if="error" class="text-red-600 py-4">{{ error.message }}</div>
    <div v-else-if="data" class="overflow-x-auto bg-white rounded-lg border border-gray-200">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="px-4 py-2 text-left font-medium">Rank</th>
            <th class="px-4 py-2 text-left font-medium">Números</th>
            <th class="px-4 py-2 text-right font-medium">Contagem</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(combo, i) in data.combinations"
            :key="i"
            class="border-b border-gray-100 hover:bg-gray-50"
          >
            <td class="px-4 py-2 text-gray-400 tabular-nums">{{ i + 1 }}</td>
            <td class="px-4 py-2 font-mono">{{ combo.numbers.join(', ') }}</td>
            <td class="px-4 py-2 text-right tabular-nums">{{ combo.count }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
