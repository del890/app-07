<script setup>
/**
 * SText — body & utility text (Inter). One component covers paragraphs,
 * labels, captions and eyebrows via `size`, `weight`, `tone` and `variant`.
 */
const props = defineProps({
  as: { type: String, default: 'p' },
  size: { type: String, default: 'md' },      // 2xs..xl
  weight: { type: String, default: 'regular' }, // regular|medium|semibold|bold
  tone: { type: String, default: 'default' },   // default|muted|subtle|brand|success|danger
  variant: { type: String, default: null },     // 'eyebrow' for all-caps tracked labels
  align: { type: String, default: null },
});
</script>

<template>
  <component
    :is="as"
    class="s-text"
    :class="[
      `s-text--${size}`,
      `s-text--w-${weight}`,
      `s-text--${tone}`,
      variant && `s-text--${variant}`,
      align && `s-text--${align}`,
    ]"
  >
    <slot />
  </component>
</template>

<style scoped>
.s-text {
  font-family: var(--font-body);
  line-height: var(--line-normal);
  color: var(--color-text);
  margin: 0;
  text-wrap: pretty;
}

.s-text--2xs { font-size: var(--font-size-2xs); }
.s-text--xs  { font-size: var(--font-size-xs); }
.s-text--sm  { font-size: var(--font-size-sm); }
.s-text--md  { font-size: var(--font-size-md); }
.s-text--lg  { font-size: var(--font-size-lg); }
.s-text--xl  { font-size: var(--font-size-xl); line-height: var(--line-snug); }

.s-text--w-regular  { font-weight: var(--font-weight-regular); }
.s-text--w-medium   { font-weight: var(--font-weight-medium); }
.s-text--w-semibold { font-weight: var(--font-weight-semibold); }
.s-text--w-bold     { font-weight: var(--font-weight-bold); }

.s-text--default { color: var(--color-text); }
.s-text--muted   { color: var(--color-text-muted); }
.s-text--subtle  { color: var(--color-text-subtle); }
.s-text--brand   { color: var(--color-primary); }
.s-text--success { color: var(--color-success); }
.s-text--danger  { color: var(--color-danger); }

.s-text--eyebrow {
  text-transform: uppercase;
  letter-spacing: var(--tracking-caps);
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-xs);
  color: var(--color-primary);
}

.s-text--start { text-align: start; }
.s-text--center { text-align: center; }
.s-text--end { text-align: end; }
</style>
