<script setup lang="ts">
import { useActiveGame, type ActiveGame } from '~/composables/useActiveGame'

const router = useRouter()
const { activeGame, setActiveGame } = useActiveGame()

const { draws: lotofacilDraws, pending: lfPending } = useLatestDraws()
const { draws: megaSenaDraws, pending: msPending } = useLatestMegaSenaDraws()

const draws = computed(() => (activeGame.value === 'megasena' ? megaSenaDraws.value : lotofacilDraws.value))
const pending = computed(() => (activeGame.value === 'megasena' ? msPending.value : lfPending.value))
const gameLabel = computed(() => (activeGame.value === 'megasena' ? 'Mega-Sena' : 'Lotofácil'))

const gameTabs = [
  { value: 'lotofacil', label: 'Lotofácil', icon: 'star' },
  { value: 'megasena', label: 'Mega-Sena', icon: 'trophy' },
]

// Latest draw of the active game, for the sidebar snapshot.
const latest = computed(() => draws.value[0] ?? null)

function pickGame(value: string | number) {
  setActiveGame(value as ActiveGame)
}

function goResults() {
  router.push('/')
}
</script>

<template>
  <div class="container dash stack--lg stack">
    <!-- Hero banner -->
    <section class="hero">
      <SText variant="eyebrow" class="hero__eyebrow">Olá 👋</SText>
      <SHeading :level="1" size="3xl" class="hero__title">Sua sorte começa aqui</SHeading>
      <SText class="hero__sub">
        Acompanhe os últimos resultados da {{ gameLabel }} e faça a sua fezinha.
      </SText>
    </section>

    <div class="dash__grid">
      <!-- Sidebar -->
      <aside class="stack--sm stack">
        <SCard variant="brand" padding="lg">
          <div class="profile">
            <SAvatar name="Você" size="xl" ring />
            <SHeading :level="2" size="xl">Sua conta</SHeading>
            <SText size="sm" tone="muted">Apostador desde 2024</SText>
          </div>
          <template #footer>
            <SButton variant="primary" block icon="trophy" @click="goResults">Ver resultados</SButton>
          </template>
        </SCard>

        <SCard variant="outlined" padding="md">
          <div class="row-between">
            <SText size="sm" weight="semibold" as="span">Jogo ativo</SText>
            <SBadge variant="brand" tone="soft">{{ gameLabel }}</SBadge>
          </div>
          <SDivider />
          <div v-if="latest" class="stack--xs stack">
            <SText size="xs" tone="muted" as="span">Último concurso</SText>
            <div class="row row--tight">
              <SLotteryBall :number="activeGame === 'megasena' ? 6 : 15" size="sm" />
              <SText weight="semibold" as="span">Concurso {{ latest.concurso }}</SText>
            </div>
            <SText size="xs" tone="muted" as="span">{{ latest.data }}</SText>
          </div>
          <SText v-else size="sm" tone="muted">Carregando…</SText>
        </SCard>
      </aside>

      <!-- Main column -->
      <section class="stack--sm stack">
        <div class="row-between">
          <SHeading :level="2" size="2xl">Resultados recentes</SHeading>
          <STabs :model-value="activeGame" :items="gameTabs" variant="pill" @update:model-value="pickGame" />
        </div>

        <!-- Loading -->
        <div v-if="pending" class="stack--sm stack">
          <SCard v-for="n in 2" :key="n" variant="elevated" padding="md">
            <div class="skeleton skeleton--line" />
            <div class="balls" style="margin-block-start: var(--space-3);">
              <div v-for="i in (activeGame === 'megasena' ? 6 : 15)" :key="i" class="skeleton skeleton--ball" />
            </div>
          </SCard>
        </div>

        <!-- Recent draw cards -->
        <template v-else>
          <SCard v-for="draw in draws.slice(0, 3)" :key="draw.concurso" variant="elevated" padding="md">
            <div class="draw">
              <SLotteryBall :number="draw.dezenas?.length ? parseInt(draw.dezenas[0]!) : 7" size="md" />
              <div class="draw__body stack--xs stack">
                <div class="row row--tight">
                  <SHeading :level="3" size="xl">Concurso {{ draw.concurso }}</SHeading>
                  <SBadge v-if="draw.acumulou" variant="danger" tone="soft">Acumulou</SBadge>
                </div>
                <SText size="sm" tone="muted" as="span">{{ draw.data }}</SText>
                <div class="balls" style="margin-block-start: var(--space-1);">
                  <SLotteryBall v-for="num in draw.dezenas" :key="num" :number="parseInt(num)" size="sm" />
                </div>
              </div>
              <SButton variant="ghost" pill icon-end="chevron-right" class="draw__cta" @click="goResults">
                Detalhes
              </SButton>
            </div>
          </SCard>

          <SButton variant="ghost" block @click="goResults">Ver todos os resultados</SButton>
        </template>
      </section>
    </div>
  </div>
</template>

<style scoped>
.dash { padding-block: var(--space-2); }

.hero {
  padding: var(--space-7) var(--space-6);
  border-radius: var(--radius-xl);
  background: linear-gradient(160deg, var(--color-primary), color-mix(in oklab, var(--color-primary) 55%, black));
  color: #fff;
  box-shadow: var(--shadow-md);
}
.hero__eyebrow { color: rgba(255, 255, 255, 0.85); }
.hero__title { color: #fff; margin-block: var(--space-2); }
.hero__sub { color: rgba(255, 255, 255, 0.9); max-inline-size: 44ch; }

.dash__grid {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: var(--space-5);
  align-items: start;
}
@media (max-width: 820px) {
  .dash__grid { grid-template-columns: 1fr; }
}

.profile { display: flex; flex-direction: column; align-items: center; gap: var(--space-1); text-align: center; }
.profile :deep(.s-avatar) { margin-block-end: var(--space-2); }

.draw { display: flex; align-items: center; gap: var(--space-4); }
.draw__body { flex: 1; min-inline-size: 0; }
.draw__cta { flex: none; align-self: flex-start; }
@media (max-width: 520px) {
  .draw { flex-wrap: wrap; }
  .draw__cta { align-self: stretch; }
}

.skeleton {
  background: linear-gradient(90deg, var(--color-surface-sunken), var(--color-border-subtle), var(--color-surface-sunken));
  background-size: 200% 100%;
  border-radius: var(--radius-sm);
  animation: dash-skel 1.3s ease-in-out infinite;
}
.skeleton--line { block-size: 1.25rem; inline-size: 10rem; }
.skeleton--ball { inline-size: 2rem; block-size: 2rem; border-radius: var(--radius-circle); }
@keyframes dash-skel { to { background-position: -200% 0; } }
</style>
