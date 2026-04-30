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
  <div>
    <h1 class="text-2xl font-bold mb-2">Modo Pesquisa</h1>
    <p class="text-gray-500 mb-6 text-sm">
      Análise estatística de sorteios históricos da Lotofácil. Todos os resultados possuem
      <span class="font-medium text-amber-700">artifact_type: research</span> — apenas para entretenimento.
    </p>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <NuxtLink
        v-for="view in views"
        :key="view.to"
        :to="view.to"
        class="block p-5 bg-white rounded-lg border border-gray-200 hover:border-blue-400 hover:shadow-sm transition-all"
      >
        <div class="font-semibold text-lg mb-1">{{ view.label }}</div>
        <div class="text-sm text-gray-500">{{ view.description }}</div>
      </NuxtLink>
    </div>
  </div>
</template>
