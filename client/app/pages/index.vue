<template>
  <div class="text-center py-12">
    <h1 class="text-3xl font-bold mb-4">Ferramenta de Pesquisa Lotofácil</h1>
    <p class="text-gray-600 mb-8 max-w-xl mx-auto">
      Explore estatísticas históricas de sorteios e pesquise padrões. Análise estatística apenas —
      nenhuma previsão é certa.
    </p>
    <div class="flex justify-center gap-4">
      <NuxtLink
        to="/research"
        class="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
      >
        Modo Pesquisa
      </NuxtLink>
      <NuxtLink
        to="/play"
        class="px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
      >
        Modo Jogar
      </NuxtLink>
    </div>
  </div>
</template>
