<script setup lang="ts">
const views = [
  { to: '/research/frequency', label: 'Frequência', description: 'Frequências por número' },
  { to: '/research/gaps', label: 'Intervalos Quente / Frio', description: 'Análise de ausências consecutivas' },
  { to: '/research/cooccurrence', label: 'Co-ocorrência', description: 'Combinações top-K de números' },
  { to: '/research/structural', label: 'Estrutural', description: 'Histogramas de soma, par/ímpar, quintil' },
  { to: '/research/order', label: 'Ordem do Sorteio', description: 'Ordem original vs canônica ordenada' },
  { to: '/research/pi-alignment', label: 'Alinhamento PI', description: 'Análise de alinhamento baseada em regras' },
  { to: '/research/correlations', label: 'Correlações de Sinais', description: 'Análise de sinais externos' },
]
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold mb-1">Modo Pesquisa</h1>
      <p class="text-muted-foreground text-sm">
        Análise estatística de sorteios históricos da Lotofácil. Todos os resultados possuem
        <span class="font-medium text-warning-foreground">artifact_type: research</span> — apenas para entretenimento.
      </p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <NuxtLink
        v-for="view in views"
        :key="view.to"
        :to="view.to"
        class="block p-5 bg-card rounded-lg border border-border border-l-4 border-l-primary/70 hover:border-primary/40 hover:border-l-primary hover:bg-primary/5 hover:shadow-lg transition-all group"
      >
        <div class="font-semibold text-lg mb-1 group-hover:text-primary transition-colors">{{ view.label }}</div>
        <div class="text-sm text-muted-foreground">{{ view.description }}</div>
      </NuxtLink>
    </div>
  </div>
</template>
