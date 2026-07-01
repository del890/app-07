<script setup>
/**
 * SLotteryBall — the signature motif: a glossy numbered lottery ball.
 * Colour follows the current theme's `--color-primary` unless you pass a
 * `lottery` id (e.g. "megasena") to pin a specific game's colour.
 */
import { computed } from 'vue';

const games = {
  lotofacil: '#930089', megasena: '#00a868', quina: '#3b1c8c', lotomania: '#f78100',
  duplasena: '#c2173a', timemania: '#6cbe45', diadesorte: '#cb8e1a', supersete: '#119e6c',
  milionaria: '#2b2a6e', federal: '#134e9c',
};

const props = defineProps({
  number: { type: [Number, String], default: '7' },
  size: { type: String, default: 'md' }, // sm | md | lg
  lottery: { type: String, default: null },
});

const color = computed(() => (props.lottery ? games[props.lottery] : 'var(--color-primary)'));
</script>

<template>
  <span class="s-ball" :class="`s-ball--${size}`" :style="{ '--_c': color }">
    <span class="s-ball__num">{{ number }}</span>
  </span>
</template>

<style scoped>
.s-ball {
  --_c: var(--color-primary);
  display: inline-grid;
  place-items: center;
  aspect-ratio: 1;
  border-radius: var(--radius-circle);
  background:
    radial-gradient(circle at 32% 28%, rgba(255, 255, 255, 0.75), rgba(255, 255, 255, 0) 42%),
    radial-gradient(circle at 70% 78%, color-mix(in oklab, var(--_c) 60%, black), var(--_c) 60%);
  box-shadow:
    inset 0 -4px 8px rgba(0, 0, 0, 0.28),
    var(--shadow-sm);
  color: #fff;
  font-family: var(--font-display);
  font-weight: var(--font-weight-extrabold);
}
.s-ball--sm { inline-size: 2rem; font-size: var(--font-size-sm); }
.s-ball--md { inline-size: 3rem; font-size: var(--font-size-lg); }
.s-ball--lg { inline-size: 4.5rem; font-size: var(--font-size-2xl); }

.s-ball__num {
  /* tiny white inner disc like a real Caixa ball */
  display: grid;
  place-items: center;
  inline-size: 64%;
  block-size: 64%;
  border-radius: inherit;
  background: rgba(255, 255, 255, 0.92);
  color: color-mix(in oklab, var(--_c) 78%, black);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.15);
}
</style>
