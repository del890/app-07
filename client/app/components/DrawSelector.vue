<script setup lang="ts">
const props = defineProps<{
  modelValue: number[]
}>()

const emit = defineEmits<{
  'update:modelValue': [numbers: number[]]
}>()

const numbers = Array.from({ length: 25 }, (_, i) => i + 1)
const selected = computed(() => new Set(props.modelValue))
const count = computed(() => props.modelValue.length)
const isFull = computed(() => count.value >= 15)
const isValid = computed(() => count.value === 15)

defineExpose({ isValid })

function toggle(n: number): void {
  if (selected.value.has(n)) {
    emit('update:modelValue', props.modelValue.filter((x) => x !== n))
  } else if (!isFull.value) {
    emit('update:modelValue', [...props.modelValue, n])
  }
}

function clearAll(): void {
  emit('update:modelValue', [])
}
</script>

<template>
  <div>
    <!-- Counter and clear button -->
    <div class="flex items-center justify-between mb-3">
      <span class="text-sm font-medium" :class="isValid ? 'text-success' : 'text-muted-foreground'">
        {{ count }} / 15 selecionados
      </span>
      <button
        type="button"
        class="text-xs text-muted-foreground hover:text-foreground underline disabled:opacity-30 disabled:cursor-not-allowed"
        :disabled="count === 0"
        @click="clearAll"
      >
        Limpar tudo
      </button>
    </div>

    <!-- 5×5 grid -->
    <div class="grid grid-cols-5 gap-2">
      <button
        v-for="n in numbers"
        :key="n"
        type="button"
        class="h-11 w-full rounded-lg text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1"
        :class="
          selected.has(n)
            ? 'bg-primary text-primary-foreground hover:bg-primary/90 focus:ring-primary'
            : isFull
              ? 'bg-muted text-muted-foreground cursor-not-allowed'
              : 'bg-muted text-foreground hover:bg-muted/70 focus:ring-ring'
        "
        :disabled="isFull && !selected.has(n)"
        :aria-pressed="selected.has(n)"
        :aria-label="`Número ${n}`"
        @click="toggle(n)"
      >
        {{ n }}
      </button>
    </div>
  </div>
</template>
