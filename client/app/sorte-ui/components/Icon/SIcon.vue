<script setup>
/**
 * SIcon — a tiny, dependency-free inline icon set drawn on a 24px grid.
 * Inherits `currentColor`, so colour follows the surrounding text.
 */
import { computed } from 'vue';

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 20 },
  /** Decorative icons are hidden from AT; pass a label to make it meaningful. */
  label: { type: String, default: '' },
});

// All paths assume stroke-based drawing on a 0 0 24 24 viewBox.
const paths = {
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  bell: '<path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6"/><path d="M9.5 19a2.5 2.5 0 0 0 5 0"/>',
  check: '<path d="m5 12 5 5 9-10"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  close: '<path d="M6 6l12 12M18 6 6 18"/>',
  menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
  'chevron-down': '<path d="m6 9 6 6 6-6"/>',
  'chevron-right': '<path d="m9 6 6 6-6 6"/>',
  'arrow-right': '<path d="M5 12h14M13 6l6 6-6 6"/>',
  star: '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8L4.5 9.7l5.9-.9z"/>',
  heart: '<path d="M12 20s-7-4.5-9.2-9A4.5 4.5 0 0 1 12 7a4.5 4.5 0 0 1 9.2 4c-2.2 4.5-9.2 9-9.2 9z"/>',
  camera: '<path d="M3 8.5A1.5 1.5 0 0 1 4.5 7H7l1.2-2h7.6L17 7h2.5A1.5 1.5 0 0 1 21 8.5v9A1.5 1.5 0 0 1 19.5 19h-15A1.5 1.5 0 0 1 3 17.5z"/><circle cx="12" cy="13" r="3.2"/>',
  video: '<rect x="3" y="6" width="12" height="12" rx="2.5"/><path d="m15 10 6-3v10l-6-3z"/>',
  brush: '<path d="M14 4l6 6-8.5 8.5a3 3 0 0 1-4.2 0l-1.8-1.8a3 3 0 0 1 0-4.2z"/><path d="M4 20s2-.5 3-1.5"/>',
  file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>',
  pencil: '<path d="M4 20l1-4L16 5l3 3L8 19z"/><path d="M14 7l3 3"/>',
  ticket: '<path d="M4 8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2 2 2 0 0 0 0 4 2 2 0 0 1-2 2H6a2 2 0 0 1-2-2 2 2 0 0 0 0-4z"/><path d="M14 6v12"/>',
  trophy: '<path d="M7 4h10v4a5 5 0 0 1-10 0z"/><path d="M7 6H4v1a3 3 0 0 0 3 3M17 6h3v1a3 3 0 0 1-3 3M9 14h6M10 20h4M12 14v6"/>',
  sparkle: '<path d="M12 3v6M12 15v6M3 12h6M15 12h6"/><path d="m6.5 6.5 3 3M14.5 14.5l3 3M17.5 6.5l-3 3M9.5 14.5l-3 3"/>',
};

const inner = computed(() => paths[props.name] ?? '');
const px = computed(() => (typeof props.size === 'number' ? `${props.size}px` : props.size));
</script>

<template>
  <svg
    class="s-icon"
    :width="px"
    :height="px"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    :role="label ? 'img' : 'presentation'"
    :aria-label="label || undefined"
    :aria-hidden="label ? undefined : 'true'"
    v-html="inner"
  />
</template>

<style scoped>
.s-icon {
  display: inline-block;
  flex: none;
  vertical-align: middle;
}
</style>
