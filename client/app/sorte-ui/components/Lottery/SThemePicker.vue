<script setup>
/**
 * SThemePicker — swatch row that sets `data-theme` on a target element
 * (default: <html>). Great for demos and real "pick your game" switchers.
 * v-model holds the active lottery id.
 */
import { lotteries } from '../../tokens.js';

const props = defineProps({
  modelValue: { type: String, default: 'lotofacil' },
  target: { type: String, default: 'root' }, // 'root' applies to <html>
});
const emit = defineEmits(['update:modelValue']);

function pick(id) {
  emit('update:modelValue', id);
  if (props.target === 'root' && typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', id);
  }
}
</script>

<template>
  <div class="s-themepicker" role="radiogroup" aria-label="Lottery theme">
    <button
      v-for="game in lotteries"
      :key="game.id"
      class="s-themepicker__swatch"
      :class="{ 'is-active': game.id === modelValue }"
      role="radio"
      type="button"
      :aria-checked="game.id === modelValue"
      :title="game.name"
      :style="{ '--_c': game.color }"
      @click="pick(game.id)"
    >
      <span class="s-themepicker__dot" />
      <span class="s-themepicker__name">{{ game.name }}</span>
    </button>
  </div>
</template>

<style scoped>
.s-themepicker { display: flex; flex-wrap: wrap; gap: var(--space-2); }
.s-themepicker__swatch {
  --_c: var(--color-primary);
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-pill);
  font-family: var(--font-display);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  color: var(--color-text);
  transition: border-color var(--dur-base) var(--ease-out), box-shadow var(--dur-base) var(--ease-out), transform var(--dur-fast) var(--ease-spring);
}
.s-themepicker__swatch:hover { transform: translateY(-1px); }
.s-themepicker__swatch.is-active {
  border-color: var(--_c);
  box-shadow: 0 0 0 3px color-mix(in oklab, var(--_c) 22%, white);
}
.s-themepicker__dot {
  inline-size: 1rem;
  block-size: 1rem;
  border-radius: var(--radius-circle);
  background: var(--_c);
  box-shadow: inset 0 -2px 3px rgba(0, 0, 0, 0.25);
}
.s-themepicker__swatch:focus-visible { outline: 3px solid var(--_c); outline-offset: 2px; }
</style>
