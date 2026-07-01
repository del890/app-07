<script setup>
/**
 * SAvatar — image, initials fallback, optional status ring.
 * Initials get a deterministic lottery-hued background so a list of users
 * looks lively without any config.
 */
import { computed } from 'vue';

const props = defineProps({
  src: { type: String, default: null },
  name: { type: String, default: '' },
  size: { type: String, default: 'md' }, // xs|sm|md|lg|xl
  status: { type: String, default: null }, // online|busy|away
  ring: { type: Boolean, default: false },
});

const palette = ['#930089', '#00a868', '#3b1c8c', '#f78100', '#c2173a', '#119e6c', '#134e9c', '#cb8e1a'];

const initials = computed(() =>
  props.name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join('') || '?'
);

const bg = computed(() => {
  const sum = [...props.name].reduce((a, c) => a + c.charCodeAt(0), 0);
  return palette[sum % palette.length];
});
</script>

<template>
  <span class="s-avatar" :class="[`s-avatar--${size}`, { 's-avatar--ring': ring }]">
    <img v-if="src" :src="src" :alt="name" class="s-avatar__img" />
    <span v-else class="s-avatar__initials" :style="{ background: bg }">{{ initials }}</span>
    <span v-if="status" class="s-avatar__status" :class="`s-avatar__status--${status}`" :aria-label="status" />
  </span>
</template>

<style scoped>
.s-avatar {
  --_size: 2.5rem;
  position: relative;
  display: inline-flex;
  inline-size: var(--_size);
  block-size: var(--_size);
  border-radius: var(--radius-circle);
  flex: none;
}
.s-avatar--xs { --_size: 1.5rem; font-size: 0.6rem; }
.s-avatar--sm { --_size: 2rem; font-size: 0.7rem; }
.s-avatar--md { --_size: 2.5rem; font-size: 0.85rem; }
.s-avatar--lg { --_size: 3.5rem; font-size: 1.1rem; }
.s-avatar--xl { --_size: 5rem; font-size: 1.6rem; }

.s-avatar--ring { box-shadow: 0 0 0 3px var(--color-surface), 0 0 0 5px var(--color-primary); }

.s-avatar__img,
.s-avatar__initials {
  inline-size: 100%;
  block-size: 100%;
  border-radius: inherit;
  object-fit: cover;
}
.s-avatar__initials {
  display: grid;
  place-items: center;
  color: #fff;
  font-family: var(--font-display);
  font-weight: var(--font-weight-bold);
}

.s-avatar__status {
  position: absolute;
  inset-block-end: 0;
  inset-inline-end: 0;
  inline-size: 30%;
  block-size: 30%;
  min-inline-size: 8px;
  min-block-size: 8px;
  border-radius: var(--radius-circle);
  box-shadow: 0 0 0 2px var(--color-surface);
}
.s-avatar__status--online { background: var(--green-500); }
.s-avatar__status--busy { background: var(--red-500); }
.s-avatar__status--away { background: var(--amber-400); }
</style>
