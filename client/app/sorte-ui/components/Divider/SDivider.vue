<script setup>
/**
 * SDivider — horizontal or vertical rule, optionally with a centred label or
 * a playful lottery-ball "dot" motif.
 */
defineProps({
  orientation: { type: String, default: 'horizontal' }, // horizontal | vertical
  variant: { type: String, default: 'line' }, // line | dotted | dashed | balls
  label: { type: String, default: null },
});
</script>

<template>
  <div
    v-if="orientation === 'horizontal'"
    class="s-divider"
    :class="[`s-divider--${variant}`, { 's-divider--labelled': label || $slots.default }]"
    role="separator"
    aria-orientation="horizontal"
  >
    <template v-if="label || $slots.default">
      <span class="s-divider__line" />
      <span class="s-divider__label"><slot>{{ label }}</slot></span>
      <span class="s-divider__line" />
    </template>
  </div>
  <div
    v-else
    class="s-divider s-divider--vertical"
    role="separator"
    aria-orientation="vertical"
  />
</template>

<style scoped>
.s-divider {
  --_color: var(--color-border);
  inline-size: 100%;
  block-size: 0;
  border-block-start: 1.5px solid var(--_color);
}
.s-divider--dotted { border-block-start-style: dotted; border-block-start-width: 2px; }
.s-divider--dashed { border-block-start-style: dashed; }

.s-divider--vertical {
  inline-size: 0;
  block-size: auto;
  align-self: stretch;
  min-block-size: 1.5rem;
  border-block-start: 0;
  border-inline-start: 1.5px solid var(--_color);
}

/* Labelled divider */
.s-divider--labelled {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  border: 0;
}
.s-divider__line {
  flex: 1;
  block-size: 0;
  border-block-start: 1.5px solid var(--_color);
}
.s-divider--dotted .s-divider__line { border-block-start-style: dotted; border-block-start-width: 2px; }
.s-divider--dashed .s-divider__line { border-block-start-style: dashed; }
.s-divider__label {
  font-family: var(--font-display);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-caps);
  color: var(--color-text-muted);
}

/* "balls" — a string of lottery balls instead of a flat line */
.s-divider--balls {
  border: 0;
  block-size: 8px;
  background-image: radial-gradient(circle, var(--color-primary) 38%, transparent 42%);
  background-size: 16px 8px;
  background-repeat: repeat-x;
  background-position: center;
  opacity: 0.85;
}
.s-divider--balls.s-divider--labelled { background: none; }
.s-divider--balls .s-divider__line {
  border: 0;
  block-size: 8px;
  background-image: radial-gradient(circle, var(--color-primary) 38%, transparent 42%);
  background-size: 16px 8px;
  background-repeat: repeat-x;
  background-position: center;
}
</style>
