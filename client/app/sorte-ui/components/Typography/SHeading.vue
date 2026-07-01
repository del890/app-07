<script setup>
/**
 * SHeading — display typography (Poppins). `level` sets the semantic tag,
 * `size` sets the visual scale; they're decoupled so you keep a correct
 * document outline without sacrificing the look.
 */
import { computed } from 'vue';

const props = defineProps({
  level: { type: [Number, String], default: 2 },
  size: { type: String, default: null }, // 'xl' | '2xl' | '3xl' | '4xl'
  align: { type: String, default: null }, // 'start' | 'center' | 'end'
});

const tag = computed(() => `h${props.level}`);
const sizeClass = computed(() => `s-heading--${props.size ?? `h${props.level}`}`);
</script>

<template>
  <component
    :is="tag"
    class="s-heading"
    :class="[sizeClass, align && `s-heading--${align}`]"
  >
    <slot />
  </component>
</template>

<style scoped>
.s-heading {
  font-family: var(--font-display);
  font-weight: var(--font-weight-extrabold);
  line-height: var(--line-tight);
  letter-spacing: var(--tracking-tight);
  color: var(--color-text);
  text-wrap: balance;
}

.s-heading--h1, .s-heading--4xl { font-size: var(--font-size-4xl); }
.s-heading--h2, .s-heading--3xl { font-size: var(--font-size-3xl); }
.s-heading--h3, .s-heading--2xl { font-size: var(--font-size-2xl); }
.s-heading--h4, .s-heading--xl  { font-size: var(--font-size-xl); font-weight: var(--font-weight-bold); }
.s-heading--h5 { font-size: var(--font-size-lg); font-weight: var(--font-weight-bold); }
.s-heading--h6 { font-size: var(--font-size-md); font-weight: var(--font-weight-bold); }

.s-heading--start { text-align: start; }
.s-heading--center { text-align: center; }
.s-heading--end { text-align: end; }
</style>
