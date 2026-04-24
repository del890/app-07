<script setup lang="ts">
import type { OrderResult } from '~/types/api'

const { get } = useApi()

const { data, pending, error } = await useAsyncData<OrderResult>(
  'order',
  () => get('/v1/statistics/order'),
)
</script>

<template>
  <div>
    <NuxtLink to="/research" class="text-sm text-blue-600 hover:underline mb-4 block">← Research</NuxtLink>
    <h1 class="text-2xl font-bold mb-4">Draw Order Analysis</h1>

    <div v-if="pending" class="text-gray-400 py-8 text-center">Loading…</div>
    <div v-else-if="error" class="text-red-600 py-4">{{ error.message }}</div>
    <div v-else-if="data" class="bg-white rounded-lg border border-gray-200 p-6 max-w-lg">
      <div class="flex items-center gap-3 mb-4">
        <span
          class="px-3 py-1 rounded-full text-sm font-semibold"
          :class="data.order_is_original ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'"
        >
          {{ data.order_is_original ? 'Original draw order' : 'Sorted-canonical order' }}
        </span>
      </div>
      <p class="text-gray-600 text-sm">{{ data.label }}</p>
      <p class="mt-4 text-xs text-gray-400">
        "Sorted-canonical" means numbers are stored in ascending order, which is the norm for
        most public datasets. Original draw order is preserved only when the source encodes it.
      </p>
    </div>
  </div>
</template>
