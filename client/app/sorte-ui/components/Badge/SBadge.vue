<script setup>
/**
 * SBadge — pills for status, counts and labels.
 * variant: brand | neutral | success | warning | danger | info | accent
 * tone:    solid | soft (default) | outline
 */
import SIcon from '../Icon/SIcon.vue';

defineProps({
  variant: { type: String, default: 'neutral' },
  tone: { type: String, default: 'soft' },
  size: { type: String, default: 'md' }, // sm | md
  icon: { type: String, default: null },
  dot: { type: Boolean, default: false },
  pill: { type: Boolean, default: true },
});
</script>

<template>
  <span
    class="s-badge"
    :class="[`s-badge--${variant}`, `s-badge--${tone}`, `s-badge--${size}`, { 's-badge--square': !pill }]"
  >
    <span v-if="dot" class="s-badge__dot" aria-hidden="true" />
    <SIcon v-if="icon" :name="icon" :size="size === 'sm' ? 12 : 14" />
    <slot />
  </span>
</template>

<style scoped>
.s-badge {
  --_c: var(--neutral-600);
  --_soft: var(--neutral-100);
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-family: var(--font-body);
  font-weight: var(--font-weight-semibold);
  line-height: 1;
  border-radius: var(--radius-pill);
  white-space: nowrap;
}
.s-badge--square { border-radius: var(--radius-xs); }
.s-badge--sm { font-size: var(--font-size-2xs); padding: 0.2rem 0.5rem; }
.s-badge--md { font-size: var(--font-size-xs); padding: 0.3rem 0.65rem; }

.s-badge--brand   { --_c: var(--color-primary-stronger); --_soft: var(--color-primary-soft); }
.s-badge--neutral { --_c: var(--neutral-600); --_soft: var(--neutral-100); }
.s-badge--success { --_c: var(--green-700); --_soft: var(--green-100); }
.s-badge--warning { --_c: #8a6400; --_soft: var(--amber-100); }
.s-badge--danger  { --_c: var(--red-600); --_soft: var(--red-100); }
.s-badge--info    { --_c: #1c4fbf; --_soft: var(--blue-100); }
.s-badge--accent  { --_c: var(--orange-600); --_soft: var(--orange-100); }

.s-badge--soft    { background: var(--_soft); color: var(--_c); }
.s-badge--solid   { background: var(--_c); color: #fff; }
.s-badge--outline { background: transparent; color: var(--_c); box-shadow: inset 0 0 0 1.5px currentColor; }

.s-badge__dot {
  inline-size: 0.5em;
  block-size: 0.5em;
  border-radius: var(--radius-circle);
  background: currentColor;
}
</style>
