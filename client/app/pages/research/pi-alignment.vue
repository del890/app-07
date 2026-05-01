<script setup lang="ts">
import type { PiAlignmentResult } from '~/types/api'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'

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
  <div class="space-y-6">
    <div>
      <Button variant="ghost" as-child class="-ml-3 mb-1">
        <NuxtLink to="/research">← Pesquisa</NuxtLink>
      </Button>
      <h1 class="text-2xl font-bold">Análise de Alinhamento PI</h1>
    </div>

    <div class="flex flex-wrap items-center gap-4 text-sm">
      <label class="flex items-center gap-2">
        Regra
        <Select v-model="selectedRule">
          <SelectTrigger class="w-52">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="r in rules" :key="r" :value="r">{{ r }}</SelectItem>
          </SelectContent>
        </Select>
      </label>
      <label class="flex items-center gap-2">
        Índice alvo
        <Input
          v-model="targetInput"
          type="number"
          min="0"
          placeholder="(sorteio mais recente)"
          class="w-36"
          @keydown.enter="applyTarget"
        />
        <Button size="sm" @click="applyTarget">Aplicar</Button>
      </label>
    </div>

    <div v-if="pending" class="text-muted-foreground py-8 text-center">Carregando…</div>
    <div v-else-if="error" class="text-destructive py-4">{{ error.message }}</div>
    <div v-else-if="data" class="bg-card rounded-lg border p-6 max-w-2xl">
      <div class="flex items-center gap-3 mb-3">
        <span class="text-xs font-mono bg-muted px-2 py-0.5 rounded">{{ data.rule }}</span>
        <span class="text-2xl font-bold tabular-nums">{{ data.score.toFixed(4) }}</span>
        <span class="text-xs text-muted-foreground">pontuação de alinhamento</span>
      </div>
      <p class="text-sm">{{ data.explanation }}</p>
    </div>
  </div>
</template>
