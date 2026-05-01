<script setup lang="ts">
import { cn } from '~/lib/utils'
import { Badge } from '~/components/ui/badge'

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
  if (c >= 0.7) return 'bg-success/15 text-success border-success/30'
  if (c >= 0.4) return 'bg-warning/15 text-warning border-warning/30'
  return 'bg-destructive/15 text-destructive border-destructive/30'
})
</script>

<template>
  <Badge
    v-if="isValid"
    variant="outline"
    :class="cn('gap-1 font-semibold', colorClass)"
    :title="`Confiança: ${percentage}%`"
    aria-label="Índice de confiança"
  >
    {{ percentage }}%
  </Badge>
  <!-- Render nothing if confidence is missing or invalid — per spec 11.5 -->
</template>
