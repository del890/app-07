<script setup lang="ts">
import type { CooccurrenceResult } from '~/types/api'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'

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
  <div class="space-y-6">
    <div>
      <Button variant="ghost" as-child class="-ml-3 mb-1">
        <NuxtLink to="/research">← Pesquisa</NuxtLink>
      </Button>
      <h1 class="text-2xl font-bold">Explorador de Co-ocorrência</h1>
    </div>

    <div class="flex flex-wrap items-center gap-4 text-sm">
      <label class="flex items-center gap-2">
        Arity
        <Select v-model="arity" @update:model-value="(v) => (arity = Number(v))">
          <SelectTrigger class="w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="2">Pares (2)</SelectItem>
            <SelectItem value="3">Trios (3)</SelectItem>
            <SelectItem value="4">Quádruplos (4)</SelectItem>
          </SelectContent>
        </Select>
      </label>
      <label class="flex items-center gap-2">
        Top K
        <Input v-model.number="topK" type="number" min="1" max="500" class="w-20" />
      </label>
    </div>

    <div v-if="pending" class="text-muted-foreground py-8 text-center">Carregando…</div>
    <div v-else-if="error" class="text-destructive py-4">{{ error.message }}</div>
    <div v-else-if="data" class="overflow-x-auto bg-card rounded-lg border">
      <table class="w-full text-sm">
        <thead class="bg-muted border-b">
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
            class="border-b hover:bg-muted/30"
          >
            <td class="px-4 py-2 text-muted-foreground tabular-nums">{{ i + 1 }}</td>
            <td class="px-4 py-2 font-mono">{{ combo.numbers.join(', ') }}</td>
            <td class="px-4 py-2 text-right tabular-nums">{{ combo.count }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
