<script setup>
/**
 * SAppHeader — top application bar. Slots:
 *   brand    — logo / wordmark (falls back to `brand` prop text)
 *   nav      — primary navigation links
 *   default  — center area (e.g. a search field)
 *   actions  — right-side actions (buttons, avatar, bell…)
 *
 * variant: light (default) | ink (dark) | brand (lottery-tinted)
 */
defineProps({
  brand: { type: String, default: 'Sorte' },
  variant: { type: String, default: 'light' },
  sticky: { type: Boolean, default: false },
});
</script>

<template>
  <header class="s-appbar" :class="[`s-appbar--${variant}`, { 's-appbar--sticky': sticky }]">
    <div class="s-appbar__inner">
      <div class="s-appbar__brand">
        <slot name="brand">
          <span class="s-appbar__logo" aria-hidden="true" />
          <span class="s-appbar__wordmark">{{ brand }}</span>
        </slot>
      </div>
      <nav v-if="$slots.nav" class="s-appbar__nav"><slot name="nav" /></nav>
      <div v-if="$slots.default" class="s-appbar__center"><slot /></div>
      <div v-if="$slots.actions" class="s-appbar__actions"><slot name="actions" /></div>
    </div>
  </header>
</template>

<style scoped>
.s-appbar {
  --_bg: var(--color-surface);
  --_fg: var(--color-text);
  background: var(--_bg);
  color: var(--_fg);
  border-block-end: 1.5px solid var(--color-border-subtle);
}
.s-appbar--ink {
  --_bg: var(--neutral-900);
  --_fg: #fff;
  border-block-end-color: transparent;
}
.s-appbar--brand {
  --_bg: var(--color-primary);
  --_fg: var(--color-primary-contrast);
  border-block-end-color: transparent;
}
.s-appbar--sticky { position: sticky; inset-block-start: 0; z-index: 50; box-shadow: var(--shadow-sm); }

.s-appbar__inner {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  max-inline-size: var(--container-max);
  margin-inline: auto;
  padding: var(--space-3) var(--space-5);
}

.s-appbar__brand { display: flex; align-items: center; gap: var(--space-2); flex: none; }
.s-appbar__logo {
  inline-size: 2rem;
  block-size: 2rem;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  background-image: radial-gradient(circle at 30% 30%, color-mix(in oklab, var(--color-primary) 60%, white), var(--color-primary));
  box-shadow: inset 0 -3px 6px rgba(0, 0, 0, 0.2);
}
.s-appbar--brand .s-appbar__logo { background: rgba(255, 255, 255, 0.9); }
.s-appbar__wordmark {
  font-family: var(--font-display);
  font-weight: var(--font-weight-extrabold);
  font-size: var(--font-size-xl);
  letter-spacing: var(--tracking-tight);
}

.s-appbar__nav { display: flex; align-items: center; gap: var(--space-5); flex: none; }
.s-appbar__nav :slotted(a) {
  color: inherit;
  font-family: var(--font-display);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-md);
  text-decoration: none;
  opacity: 0.85;
}
.s-appbar__nav :slotted(a:hover) { opacity: 1; text-decoration: none; }

.s-appbar__center { flex: 1; min-inline-size: 0; }
.s-appbar__actions { display: flex; align-items: center; gap: var(--space-3); flex: none; margin-inline-start: auto; }

@media (max-width: 720px) {
  .s-appbar__nav, .s-appbar__center { display: none; }
}
</style>
