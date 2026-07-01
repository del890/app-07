<script setup>
/**
 * SCard — flexible surface. Compose freely with the `media`, `header`,
 * default (body) and `footer` slots, or just drop content in the default slot.
 *
 * variant:  elevated (default) | outlined | soft | brand
 * Set `interactive` (or pass `href`) for hover-lift + full-card click.
 * `accent` paints a lottery-coloured top stripe.
 */
import { computed } from 'vue';

const props = defineProps({
  variant: { type: String, default: 'elevated' },
  href: { type: String, default: null },
  interactive: { type: Boolean, default: false },
  accent: { type: Boolean, default: false },
  padding: { type: String, default: 'md' }, // none | sm | md | lg
});

const tag = computed(() => (props.href ? 'a' : 'div'));
const isInteractive = computed(() => props.interactive || !!props.href);
</script>

<template>
  <component
    :is="tag"
    class="s-card"
    :class="[
      `s-card--${variant}`,
      `s-card--pad-${padding}`,
      { 's-card--interactive': isInteractive, 's-card--accent': accent },
    ]"
    :href="href || undefined"
  >
    <div v-if="$slots.media" class="s-card__media"><slot name="media" /></div>
    <div class="s-card__inner">
      <header v-if="$slots.header" class="s-card__header"><slot name="header" /></header>
      <div v-if="$slots.default" class="s-card__body"><slot /></div>
      <footer v-if="$slots.footer" class="s-card__footer"><slot name="footer" /></footer>
    </div>
  </component>
</template>

<style scoped>
.s-card {
  position: relative;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  overflow: clip;
  color: inherit;
  text-decoration: none;
  transition:
    transform var(--dur-base) var(--ease-spring),
    box-shadow var(--dur-base) var(--ease-out),
    border-color var(--dur-base) var(--ease-out);
}

.s-card--elevated { box-shadow: var(--shadow-sm); }
.s-card--outlined { border: 1.5px solid var(--color-border); }
.s-card--soft { background: var(--color-surface-sunken); }
.s-card--brand {
  background: linear-gradient(140deg, var(--color-primary-softer), var(--color-primary-soft));
  border: 1.5px solid var(--color-primary-soft);
}

.s-card--accent::before {
  content: '';
  position: absolute;
  inset-block-start: 0;
  inset-inline: 0;
  block-size: 5px;
  background: var(--color-primary);
}

.s-card__inner {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  flex: 1;
}

.s-card--pad-none .s-card__inner { padding: 0; }
.s-card--pad-sm .s-card__inner { padding: var(--space-4); }
.s-card--pad-md .s-card__inner { padding: var(--space-5); }
.s-card--pad-lg .s-card__inner { padding: var(--space-6); }

.s-card__media { line-height: 0; }
.s-card__media :deep(img) { inline-size: 100%; object-fit: cover; }

.s-card__header { display: flex; flex-direction: column; gap: var(--space-1); }
.s-card__body { flex: 1; }
.s-card__footer { display: flex; align-items: center; gap: var(--space-3); margin-block-start: auto; }

.s-card--interactive { cursor: pointer; }
.s-card--interactive:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}
.s-card--interactive:focus-visible {
  outline: 3px solid var(--color-primary);
  outline-offset: 2px;
}
</style>
