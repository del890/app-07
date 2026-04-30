<script setup lang="ts">
const props = defineProps<{
  confidence: number | null | undefined
}>()

// Guard: refuse to render if confidence is missing or >= 1.0
const isValid = computed(() => {
  const c = props.confidence
  return c !== null && c !== undefined && c > 0 && c < 1.0
})

const percentage = computed(() => {
  if (!isValid.value) return null
  return Math.round((props.confidence as number) * 100)
})

const colorClass = computed(() => {
  const c = props.confidence as number
  if (c >= 0.7) return 'bg-green-100 text-green-800 border-green-300'
  if (c >= 0.4) return 'bg-yellow-100 text-yellow-800 border-yellow-300'
  return 'bg-red-100 text-red-800 border-red-300'
})
</script>

<template>
  <span
    v-if="isValid"
    class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-sm font-semibold border"
    :class="colorClass"
    :title="`Confiança: ${percentage}%`"
    aria-label="Índice de confiança"
  >
    {{ percentage }}%
  </span>
  <!-- Render nothing if confidence is missing or invalid — per spec 11.5 -->
</template>
