<script setup>
/**
 * SButton — the workhorse. Renders as <button> or <a> (pass `href`).
 *
 * variant: primary | secondary | success | ghost | subtle | danger | outline
 * size:    sm | md | lg
 * Plus: pill, block, loading, icon-only (use `icon` with no default slot text).
 */
import { computed } from 'vue';
import SIcon from '../Icon/SIcon.vue';

const props = defineProps({
  variant: { type: String, default: 'primary' },
  size: { type: String, default: 'md' },
  href: { type: String, default: null },
  type: { type: String, default: 'button' },
  icon: { type: String, default: null },        // leading icon name
  iconEnd: { type: String, default: null },     // trailing icon name
  iconOnly: { type: Boolean, default: false },
  pill: { type: Boolean, default: false },
  block: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  ariaLabel: { type: String, default: null },
});

const tag = computed(() => (props.href ? 'a' : 'button'));
const iconSize = computed(() => (props.size === 'lg' ? 22 : props.size === 'sm' ? 16 : 18));
</script>

<template>
  <component
    :is="tag"
    class="s-btn"
    :class="[
      `s-btn--${variant}`,
      `s-btn--${size}`,
      { 's-btn--pill': pill, 's-btn--block': block, 's-btn--loading': loading, 's-btn--icon-only': iconOnly },
    ]"
    :type="href ? undefined : type"
    :href="href && !disabled ? href : undefined"
    :aria-disabled="disabled || loading || undefined"
    :aria-busy="loading || undefined"
    :aria-label="ariaLabel || undefined"
    :disabled="!href && (disabled || loading) ? true : undefined"
    :tabindex="href && disabled ? -1 : undefined"
  >
    <span v-if="loading" class="s-btn__spinner" aria-hidden="true" />
    <SIcon v-if="icon && !loading" :name="icon" :size="iconSize" class="s-btn__icon" />
    <span v-if="!iconOnly" class="s-btn__label"><slot /></span>
    <SIcon v-if="iconEnd && !iconOnly" :name="iconEnd" :size="iconSize" class="s-btn__icon" />
  </component>
</template>

<style scoped>
.s-btn {
  --_bg: var(--color-primary);
  --_fg: var(--color-primary-contrast);
  --_bg-hover: var(--color-primary-strong);
  --_border: transparent;

  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-family: var(--font-display);
  font-weight: var(--font-weight-semibold);
  line-height: 1;
  text-decoration: none;
  white-space: nowrap;
  border: 1.5px solid var(--_border);
  border-radius: var(--radius-md);
  background: var(--_bg);
  color: var(--_fg);
  transition:
    transform var(--dur-fast) var(--ease-spring),
    background-color var(--dur-base) var(--ease-out),
    box-shadow var(--dur-base) var(--ease-out),
    border-color var(--dur-base) var(--ease-out);
  user-select: none;
}

/* Sizes — min-block-size keeps targets >= 44px on md/lg for comfy tapping */
.s-btn--sm { font-size: var(--font-size-sm); padding: 0.4rem 0.85rem; min-block-size: 34px; }
.s-btn--md { font-size: var(--font-size-md); padding: 0.6rem 1.15rem; min-block-size: 44px; }
.s-btn--lg { font-size: var(--font-size-lg); padding: 0.8rem 1.5rem; min-block-size: 52px; border-radius: var(--radius-lg); }

.s-btn--pill { border-radius: var(--radius-pill); }
.s-btn--block { display: flex; inline-size: 100%; }

.s-btn--icon-only.s-btn--sm { padding: 0.4rem; min-inline-size: 34px; }
.s-btn--icon-only.s-btn--md { padding: 0.6rem; min-inline-size: 44px; }
.s-btn--icon-only.s-btn--lg { padding: 0.8rem; min-inline-size: 52px; }

/* --- Variants -------------------------------------------------------- */
.s-btn--primary { --_bg: var(--color-primary); --_fg: var(--color-primary-contrast); --_bg-hover: var(--color-primary-strong); box-shadow: var(--shadow-sm); }
.s-btn--success { --_bg: var(--color-success); --_fg: #fff; --_bg-hover: var(--green-600); box-shadow: var(--shadow-sm); }
.s-btn--danger  { --_bg: var(--color-danger); --_fg: #fff; --_bg-hover: var(--red-600); box-shadow: var(--shadow-sm); }

.s-btn--secondary {
  --_bg: var(--color-primary-soft);
  --_fg: var(--color-primary-stronger);
  --_bg-hover: color-mix(in oklab, var(--color-primary-soft) 80%, var(--color-primary));
}

.s-btn--outline {
  --_bg: var(--color-surface);
  --_fg: var(--color-primary);
  --_border: var(--color-primary);
  --_bg-hover: var(--color-primary-softer);
}

.s-btn--ghost {
  --_bg: transparent;
  --_fg: var(--color-primary);
  --_bg-hover: var(--color-primary-softer);
}

.s-btn--subtle {
  --_bg: var(--color-surface-sunken);
  --_fg: var(--color-text);
  --_bg-hover: var(--neutral-150);
}

/* --- States ---------------------------------------------------------- */
.s-btn:hover:not([aria-disabled='true']) {
  background: var(--_bg-hover);
  transform: translateY(-1px);
}
.s-btn--outline:hover:not([aria-disabled='true']),
.s-btn--ghost:hover:not([aria-disabled='true']) {
  background: var(--_bg-hover);
}

.s-btn:active:not([aria-disabled='true']) { transform: translateY(0) scale(0.98); }

.s-btn:focus-visible {
  outline: 3px solid var(--color-primary);
  outline-offset: 2px;
}

.s-btn[aria-disabled='true'],
.s-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

.s-btn--loading { cursor: progress; }
.s-btn__label { display: inline-flex; }

.s-btn__spinner {
  inline-size: 1em;
  block-size: 1em;
  border: 2px solid currentColor;
  border-block-start-color: transparent;
  border-radius: var(--radius-circle);
  animation: s-btn-spin 0.6s linear infinite;
}

@keyframes s-btn-spin { to { transform: rotate(360deg); } }
</style>
