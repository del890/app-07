<script setup lang="ts">
import type { DrawPremio } from '~/types/api'
import { useActiveGame } from '~/composables/useActiveGame'

const { activeGame } = useActiveGame()

// Both composables are initialised at setup so data loads for both games upfront
const { draws: lotofacilDraws, pending: lfPending, error: lfError, retry: lfRetry } = useLatestDraws()
const { draws: megaSenaDraws, pending: msPending, error: msError, retry: msRetry } = useLatestMegaSenaDraws()

const draws = computed(() => activeGame.value === 'megasena' ? megaSenaDraws.value : lotofacilDraws.value)
const pending = computed(() => activeGame.value === 'megasena' ? msPending.value : lfPending.value)
const error = computed(() => activeGame.value === 'megasena' ? msError.value : lfError.value)
const retry = computed(() => activeGame.value === 'megasena' ? msRetry : lfRetry)

const badgeCount = computed(() => activeGame.value === 'megasena' ? 6 : 15)
const topPrizeLabel = computed(() => activeGame.value === 'megasena' ? '6 acertos' : '15 acertos')
const gameLabel = computed(() => activeGame.value === 'megasena' ? 'Mega-Sena' : 'Lotofácil')

function topPrize(premiacoes: DrawPremio[]): DrawPremio | undefined {
  return premiacoes.find(p => p.faixa === 1)
}

function formatCurrency(value: number): string {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}
</script>

<template>
  <div class="container container--reading stack--lg stack">
    <!-- Header -->
    <div class="stack--xs stack text-center">
      <SText variant="eyebrow" align="center">{{ gameLabel }} · Últimos Sorteios</SText>
      <SHeading :level="1" size="3xl" align="center">Resultados Recentes</SHeading>
    </div>

    <!-- Loading skeletons -->
    <div v-if="pending" class="stack">
      <SCard v-for="n in 3" :key="n" variant="outlined" padding="md">
        <div class="skeleton skeleton--title" />
        <div class="balls" style="margin-block-start: var(--space-3);">
          <div v-for="i in badgeCount" :key="i" class="skeleton skeleton--ball" />
        </div>
      </SCard>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="stack text-center" style="padding-block: var(--space-6);">
      <SText tone="danger" weight="medium">Não foi possível carregar os sorteios.</SText>
      <SText size="sm" tone="muted">{{ error.message }}</SText>
      <div class="row" style="justify-content: center;">
        <SButton variant="outline" @click="retry()">Tentar novamente</SButton>
      </div>
    </div>

    <!-- Draw cards -->
    <div v-else class="stack">
      <SCard v-for="draw in draws" :key="draw.concurso" variant="outlined" padding="lg">
        <template #header>
          <div class="row-between">
            <div class="row row--tight">
              <SHeading :level="2" size="xl">Concurso {{ draw.concurso }}</SHeading>
              <SText size="sm" tone="muted" as="span">{{ draw.data }}</SText>
            </div>
            <SBadge v-if="draw.acumulou" variant="danger" tone="soft">Acumulou</SBadge>
          </div>
        </template>

        <div class="stack--sm stack">
          <!-- Number balls -->
          <div class="balls">
            <SLotteryBall
              v-for="num in draw.dezenas"
              :key="num"
              :number="parseInt(num)"
              size="sm"
            />
          </div>
          <!-- Top prize info -->
          <div v-if="topPrize(draw.premiacoes)" class="row row--tight">
            <SText size="sm" tone="muted" as="span">{{ topPrizeLabel }}:</SText>
            <SText size="sm" weight="medium" as="span">
              {{ topPrize(draw.premiacoes)!.ganhadores }}
              {{ topPrize(draw.premiacoes)!.ganhadores === 1 ? 'ganhador' : 'ganhadores' }}
            </SText>
            <SText v-if="topPrize(draw.premiacoes)!.ganhadores > 0" size="sm" weight="semibold" tone="brand" as="span">
              {{ formatCurrency(topPrize(draw.premiacoes)!.valorPremio) }}
            </SText>
          </div>
        </div>
      </SCard>
    </div>
  </div>
</template>

<style scoped>
.skeleton {
  background: linear-gradient(90deg, var(--color-surface-sunken), var(--color-border-subtle), var(--color-surface-sunken));
  background-size: 200% 100%;
  border-radius: var(--radius-sm);
  animation: skeleton-pulse 1.3s ease-in-out infinite;
}
.skeleton--title { block-size: 1.25rem; inline-size: 8rem; }
.skeleton--ball { inline-size: 2rem; block-size: 2rem; border-radius: var(--radius-circle); }
@keyframes skeleton-pulse { to { background-position: -200% 0; } }
</style>
