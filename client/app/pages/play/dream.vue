<script setup lang="ts">
import type { DreamOracleResult, ExtractedSymbol } from '~/types/api'
import { Button } from '~/components/ui/button'

const { status, events, result, error, interpretDream, reset } = useDreamOracle()
const { saveEntry } = useDreamOracleStore()

const description = ref('')
const MAX_CHARS = 2000
const isStreaming = computed(() => status.value === 'streaming')
const isDone = computed(() => status.value === 'done')
const hasError = computed(() => status.value === 'error')
const charsLeft = computed(() => MAX_CHARS - description.value.length)
const charsWarning = computed(() => charsLeft.value < 200)

const oracleResult = computed(() => result.value as DreamOracleResult | null)

async function submit() {
  if (!description.value.trim()) return
  await interpretDream({ description: description.value.trim() })
  // Auto-save to local history once the result is ready.
  if (result.value) {
    await saveEntry({
      numbers: result.value.numbers,
      explanation: result.value.explanation,
      symbols: result.value.symbols,
      catalog_version: result.value.catalog_version,
    })
  }
}

function restart() {
  reset()
  description.value = ''
}

const INTENSITY_LABEL: Record<string, string> = {
  element: 'Elemento',
  color: 'Cor',
  emotion: 'Emoção',
  archetype: 'Arquétipo',
  count: 'Número',
}

function categoryLabel(cat: string): string {
  return INTENSITY_LABEL[cat] ?? cat
}

function intensityPercent(intensity: number): string {
  return `${Math.round(intensity * 100)}%`
}

// Cast events to any so ToolProgressTimeline receives compatible events
const timelineEvents = computed(() => events.value as any[])
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold mb-1">Oráculo dos Sonhos</h1>
      <p class="text-sm text-muted-foreground">
        Descreva um sonho, pesadelo ou situação que aconteceu. O oráculo interpreta os símbolos e sugere 15 números.
      </p>
      <p class="text-xs text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded px-3 py-1.5 mt-2 inline-block">
        Entretenimento apenas — sem base estatística ou preditiva. Jogue com responsabilidade.
      </p>
    </div>

    <!-- Input form -->
    <div v-if="status === 'idle'" class="space-y-3 max-w-xl">
      <textarea
        v-model="description"
        placeholder="Ex: Sonhei que estava voando sobre o mar enquanto o céu estava vermelho e havia um número 7 brilhando nas nuvens..."
        rows="5"
        :maxlength="MAX_CHARS"
        :disabled="isStreaming"
        class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 resize-none"
      />
      <p :class="['text-xs text-right', charsWarning ? 'text-destructive' : 'text-muted-foreground']">
        {{ charsLeft }} caracteres restantes
      </p>
      <Button
        :disabled="isStreaming || !description.trim()"
        @click="submit"
      >
        Interpretar Sonho
      </Button>
    </div>

    <!-- Streaming in progress -->
    <div v-if="isStreaming" class="space-y-2">
      <p class="text-sm text-muted-foreground animate-pulse">Interpretando símbolos do sonho…</p>
      <ToolProgressTimeline :events="timelineEvents" />
    </div>

    <!-- Error state -->
    <div v-if="hasError" class="space-y-3">
      <p class="text-sm text-destructive">{{ error }}</p>
      <Button variant="outline" @click="restart">Tentar novamente</Button>
    </div>

    <!-- Result -->
    <div v-if="isDone && oracleResult" class="space-y-8">

      <!-- Numbers -->
      <div class="rounded-xl border bg-card p-5 space-y-3">
        <div class="flex items-center gap-2">
          <span class="text-lg">🔢</span>
          <h2 class="text-base font-semibold">Números Sugeridos</h2>
        </div>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="n in [...oracleResult.numbers].sort((a, b) => a - b)"
            :key="n"
            class="inline-flex items-center justify-center w-10 h-10 rounded-full bg-primary text-primary-foreground font-bold text-sm shadow-sm"
          >
            {{ n }}
          </span>
        </div>
      </div>

      <!-- Interpretation -->
      <div class="rounded-xl border bg-card p-5 space-y-3">
        <div class="flex items-center gap-2">
          <span class="text-lg">✨</span>
          <h2 class="text-base font-semibold">Interpretação</h2>
        </div>
        <p class="text-sm text-muted-foreground leading-relaxed">
          {{ oracleResult.explanation }}
        </p>
      </div>

      <!-- Symbols found -->
      <div v-if="oracleResult.symbols.length" class="rounded-xl border bg-card p-5 space-y-4">
        <div class="flex items-center gap-2">
          <span class="text-lg">🌙</span>
          <h2 class="text-base font-semibold">Símbolos Identificados</h2>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          <div
            v-for="(sym, i) in oracleResult.symbols"
            :key="i"
            class="flex flex-col gap-2 px-4 py-3 rounded-lg border bg-background"
          >
            <div class="flex items-center justify-between">
              <span class="text-[10px] uppercase tracking-widest text-muted-foreground font-medium">
                {{ categoryLabel(sym.category) }}
              </span>
              <span class="text-[10px] font-semibold text-muted-foreground">
                {{ intensityPercent(sym.intensity) }}
              </span>
            </div>
            <span class="font-semibold text-sm capitalize leading-tight">{{ sym.label }}</span>
            <div class="h-1.5 w-full rounded-full bg-muted overflow-hidden">
              <div
                class="h-1.5 rounded-full bg-primary transition-all duration-500"
                :style="{ width: intensityPercent(sym.intensity) }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Disclaimer + action -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-1">
        <p class="text-xs text-muted-foreground max-w-sm">
          {{ oracleResult.disclaimer }}
        </p>
        <Button variant="outline" size="sm" @click="restart">Nova interpretação</Button>
      </div>

    </div>
  </div>
</template>
