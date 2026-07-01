<script setup>
/**
 * STabs — accessible tablist with an animated active underline.
 * v-model holds the active tab `value`. Items: { value, label, icon?, badge? }.
 *
 * variant: underline (default, Skillshare-style) | pill (ClassDojo-style)
 */
import SIcon from '../Icon/SIcon.vue';
import SBadge from '../Badge/SBadge.vue';

const props = defineProps({
  modelValue: { type: [String, Number], default: null },
  items: { type: Array, required: true },
  variant: { type: String, default: 'underline' },
});
const emit = defineEmits(['update:modelValue']);

function select(item) {
  if (item.disabled) return;
  emit('update:modelValue', item.value);
}
function onKey(e, index) {
  const dir = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
  if (!dir) return;
  e.preventDefault();
  const next = (index + dir + props.items.length) % props.items.length;
  select(props.items[next]);
  e.currentTarget.parentElement?.children[next]?.focus();
}
</script>

<template>
  <div class="s-tabs" :class="`s-tabs--${variant}`" role="tablist">
    <button
      v-for="(item, i) in items"
      :key="item.value"
      class="s-tabs__tab"
      :class="{ 'is-active': item.value === modelValue }"
      role="tab"
      type="button"
      :aria-selected="item.value === modelValue"
      :tabindex="item.value === modelValue ? 0 : -1"
      :disabled="item.disabled || undefined"
      @click="select(item)"
      @keydown="onKey($event, i)"
    >
      <SIcon v-if="item.icon" :name="item.icon" :size="18" />
      <span>{{ item.label }}</span>
      <SBadge v-if="item.badge != null" size="sm" variant="brand">{{ item.badge }}</SBadge>
    </button>
  </div>
</template>

<style scoped>
.s-tabs {
  display: flex;
  gap: var(--space-1);
  flex-wrap: wrap;
}
.s-tabs--underline {
  gap: var(--space-5);
  border-block-end: 1.5px solid var(--color-border);
}

.s-tabs__tab {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  background: transparent;
  border: 0;
  font-family: var(--font-display);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-md);
  color: var(--color-text-muted);
  transition: color var(--dur-base) var(--ease-out), background var(--dur-base) var(--ease-out);
}
.s-tabs__tab:disabled { opacity: 0.45; cursor: not-allowed; }

/* underline variant */
.s-tabs--underline .s-tabs__tab {
  padding-block: var(--space-3);
  position: relative;
}
.s-tabs--underline .s-tabs__tab::after {
  content: '';
  position: absolute;
  inset-block-end: -1.5px;
  inset-inline: 0;
  block-size: 3px;
  border-radius: var(--radius-pill);
  background: var(--color-primary);
  transform: scaleX(0);
  transition: transform var(--dur-base) var(--ease-spring);
}
.s-tabs--underline .s-tabs__tab.is-active { color: var(--color-primary); }
.s-tabs--underline .s-tabs__tab.is-active::after { transform: scaleX(1); }

/* pill variant */
.s-tabs--pill { gap: var(--space-1); padding: var(--space-1); background: var(--color-surface-sunken); border-radius: var(--radius-pill); inline-size: fit-content; }
.s-tabs--pill .s-tabs__tab { padding: var(--space-2) var(--space-4); border-radius: var(--radius-pill); }
.s-tabs--pill .s-tabs__tab:hover:not(:disabled):not(.is-active) { color: var(--color-text); }
.s-tabs--pill .s-tabs__tab.is-active { background: var(--color-surface); color: var(--color-primary); box-shadow: var(--shadow-xs); }

.s-tabs__tab:focus-visible { outline: 3px solid var(--color-primary); outline-offset: 2px; border-radius: var(--radius-sm); }
</style>
