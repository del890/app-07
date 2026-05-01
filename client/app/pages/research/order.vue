<script setup lang="ts">
import type { OrderResult } from '~/types/api'
import { Button } from '~/components/ui/button'

const { get } = useApi()

const { data, pending, error } = await useAsyncData<OrderResult>(
  'order',
  () => get('/v1/statistics/order'),
)
</script>

<template>
  <div class="space-y-6">
    <div>
      <Button variant="ghost" as-child class="-ml-3 mb-1">
        <NuxtLink to="/research">← Pesquisa</NuxtLink>
      </Button>
      <h1 class="text-2xl font-bold">Análise de Ordem do Sorteio</h1>
    </div>

    <div v-if="pending" class="text-muted-foreground py-8 text-center">Carregando…</div>
    <div v-else-if="error" class="text-destructive py-4">{{ error.message }}</div>
    <div v-else-if="data" class="bg-card rounded-lg border p-6 max-w-lg">
      <div class="flex items-center gap-3 mb-4">
        <span
          class="px-3 py-1 rounded-full text-sm font-semibold"
          :class="data.order_is_original ? 'bg-success/15 text-success' : 'bg-warning/15 text-warning-foreground'"
        >
          {{ data.order_is_original ? 'Ordem original do sorteio' : 'Ordem canônica ordenada' }}
        </span>
      </div>
      <p class="text-sm">{{ data.label }}</p>
      <p class="mt-4 text-xs text-muted-foreground">
        "Ordem canônica ordenada" significa que os números são armazenados em ordem crescente, que é o padrão para
        a maioria dos conjuntos de dados públicos. A ordem original do sorteio é preservada apenas quando a fonte a codifica.
      </p>
    </div>
  </div>
</template>
