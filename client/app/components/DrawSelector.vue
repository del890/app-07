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
      <span class="text-sm font-medium" :class="isValid ? 'text-green-600' : 'text-gray-600'">
        {{ count }} / 15 selecionados
      </span>
      <button
        type="button"
        class="text-xs text-gray-400 hover:text-gray-600 underline disabled:opacity-30 disabled:cursor-not-allowed"
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
            ? 'bg-purple-600 text-white hover:bg-purple-700 focus:ring-purple-500'
            : isFull
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200 focus:ring-gray-400'
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
