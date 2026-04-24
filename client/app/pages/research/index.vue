<script setup lang="ts">
const views = [
  { to: '/research/frequency', label: 'Frequency', description: 'Per-number draw frequencies' },
  { to: '/research/gaps', label: 'Hot / Cold Gaps', description: 'Consecutive-absence analysis' },
  { to: '/research/cooccurrence', label: 'Co-occurrence', description: 'Top-K number combinations' },
  { to: '/research/structural', label: 'Structural', description: 'Sum, even/odd, quintile histograms' },
  { to: '/research/order', label: 'Draw Order', description: 'Original vs sorted-canonical order' },
  { to: '/research/pi-alignment', label: 'PI Alignment', description: 'Rule-based alignment analysis' },
  { to: '/research/correlations', label: 'Signal Correlations', description: 'External signal analysis' },
]
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-2">Research Mode</h1>
    <p class="text-gray-500 mb-6 text-sm">
      Statistical analysis of historical Lotofácil draws. All outputs carry
      <span class="font-medium text-amber-700">artifact_type: research</span> — for entertainment only.
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
