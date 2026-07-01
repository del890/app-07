<script setup lang="ts">
import { useActiveGame, type ActiveGame } from '~/composables/useActiveGame'

const route = useRoute()
const { activeGame, setActiveGame } = useActiveGame()

// Drive the whole UI's colour scheme from the active game via Sorte UI's
// `data-theme` system: lotofácil → violet, mega-sena → green.
watchEffect(() => {
  if (import.meta.client) {
    document.documentElement.setAttribute('data-theme', activeGame.value)
  }
})

const isHome = computed(() => route.path === '/')
const isDashboard = computed(() => route.path.startsWith('/dashboard'))

// Switching the game just re-skins in place — no navigation.
function switchGame(game: ActiveGame) {
  setActiveGame(game)
}
</script>

<template>
  <div class="app-shell">
    <SAppHeader sticky>
      <template #brand>
        <NuxtLink to="/" class="brand">
          <SLotteryBall :number="activeGame === 'megasena' ? 6 : 15" size="sm" />
          <span class="brand__word">Fezinha</span>
        </NuxtLink>
      </template>

      <template #nav>
        <NuxtLink to="/" class="nav-pill" :class="{ 'is-active': isHome }">Início</NuxtLink>
        <NuxtLink to="/dashboard" class="nav-pill" :class="{ 'is-active': isDashboard }">Painel</NuxtLink>
        <span class="nav-sep" aria-hidden="true" />
        <button
          type="button"
          class="nav-pill"
          :class="{ 'is-active': activeGame === 'lotofacil' }"
          @click="switchGame('lotofacil')"
        >
          Lotofácil
        </button>
        <button
          type="button"
          class="nav-pill"
          :class="{ 'is-active': activeGame === 'megasena' }"
          @click="switchGame('megasena')"
        >
          Mega-Sena
        </button>
      </template>
    </SAppHeader>

    <main class="container app-main">
      <slot />
    </main>

    <footer class="app-footer">
      <SText size="2xs" tone="muted" variant="eyebrow" as="span">
        Loteca Premiada — não afiliada à Caixa Econômica Federal
      </SText>
    </footer>

    <!-- Mobile bottom tab bar -->
    <nav class="tabbar">
      <NuxtLink to="/" class="tabbar__item" :class="{ 'is-active': isHome }">
        <SIcon name="trophy" :size="20" />
        Início
      </NuxtLink>
      <NuxtLink to="/dashboard" class="tabbar__item" :class="{ 'is-active': isDashboard }">
        <SIcon name="sparkle" :size="20" />
        Painel
      </NuxtLink>
      <button type="button" class="tabbar__item" :class="{ 'is-active': activeGame === 'lotofacil' }" @click="switchGame('lotofacil')">
        <SIcon name="star" :size="20" />
        Lotofácil
      </button>
      <button type="button" class="tabbar__item" :class="{ 'is-active': activeGame === 'megasena' }" @click="switchGame('megasena')">
        <SIcon name="ticket" :size="20" />
        Mega-Sena
      </button>
    </nav>
  </div>
</template>

<style scoped>
.brand { display: inline-flex; align-items: center; gap: var(--space-2); text-decoration: none; }
.brand__word {
  font-family: var(--font-display);
  font-weight: var(--font-weight-extrabold);
  font-size: var(--font-size-xl);
  letter-spacing: var(--tracking-tight);
  color: var(--color-text);
}

.nav-sep {
  inline-size: 1.5px;
  block-size: 1.5rem;
  background: var(--color-border);
  margin-inline: var(--space-1);
}

.nav-pill {
  display: inline-flex;
  align-items: center;
  padding: var(--space-2) var(--space-4);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-pill);
  background: transparent;
  font-family: var(--font-display);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  color: var(--color-text);
  text-decoration: none;
  transition: border-color var(--dur-base) var(--ease-out), background var(--dur-base) var(--ease-out), color var(--dur-base) var(--ease-out);
}
.nav-pill:hover { border-color: var(--color-primary); text-decoration: none; }
.nav-pill.is-active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-primary-contrast);
}

.app-main {
  flex: 1;
  inline-size: 100%;
  padding-block: var(--space-6);
  padding-block-end: calc(var(--space-9) + env(safe-area-inset-bottom, 0px));
}
@media (min-width: 721px) {
  .app-main { padding-block-end: var(--space-6); }
}

.app-footer {
  padding: var(--space-4);
  text-align: center;
  border-block-start: 1.5px solid var(--color-border-subtle);
}

/* Mobile bottom tab bar */
.tabbar {
  position: fixed;
  inset-inline: 0;
  inset-block-end: 0;
  z-index: 50;
  display: flex;
  background: var(--color-surface);
  border-block-start: 1.5px solid var(--color-border);
  padding-block-end: env(safe-area-inset-bottom, 0px);
}
.tabbar__item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  min-block-size: 56px;
  border: 0;
  border-block-start: 2px solid transparent;
  background: transparent;
  font-family: var(--font-display);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-2xs);
  color: var(--color-text-muted);
  text-decoration: none;
}
.tabbar__item.is-active { color: var(--color-primary); border-block-start-color: var(--color-primary); }
@media (min-width: 721px) {
  .tabbar { display: none; }
}
</style>
