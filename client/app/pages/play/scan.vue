<script setup lang="ts">
import { Button } from '~/components/ui/button'

useHead({ title: 'Escanear Volante — Lotofácil' })

const router = useRouter()

async function handleConfirm(numbers: number[]): Promise<void> {
  // Pre-populate the My Draw preload state so the page opens with these numbers
  const preload = useState<number[] | null>('my-draw.preload')
  preload.value = numbers

  // Fire-and-forget save (no analysis profile available at this point)
  // The My Draw page will trigger analysis and auto-save with the full profile
  await router.push('/play/my-draw')
}
</script>

<template>
  <div class="space-y-5">
    <div>
      <Button variant="ghost" as-child class="-ml-3 mb-1">
        <NuxtLink to="/play/my-draw">← Meu Volante</NuxtLink>
      </Button>
      <h1 class="text-2xl font-bold mb-1">Escanear Volante</h1>
      <p class="text-sm text-muted-foreground">
        Aponte a câmera para um volante da Lotofácil preenchido. O app lerá os números marcados
        automaticamente.
      </p>
    </div>

    <!-- Positioning guide -->
    <div class="w-full">
      <p class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
        Como posicionar o volante
      </p>
      <div class="flex gap-2">
        <!-- Card 1: Correct -->
        <div class="flex-1 flex flex-col items-center gap-1.5 bg-success/10 border border-success/30 rounded-xl p-2">
          <svg viewBox="0 0 60 72" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto">
            <!-- Camera frame -->
            <rect x="2" y="2" width="56" height="68" rx="3" fill="#f3f4f6" stroke="#d1d5db" stroke-width="1"/>
            <!-- Ticket rect (nicely centred) -->
            <rect x="16" y="11" width="28" height="50" rx="2" fill="white" stroke="#6b7280" stroke-width="1.5"/>
            <!-- Grid lines suggesting ticket content -->
            <line x1="20" y1="24" x2="40" y2="24" stroke="#e5e7eb" stroke-width="1"/>
            <line x1="20" y1="33" x2="40" y2="33" stroke="#e5e7eb" stroke-width="1"/>
            <line x1="20" y1="42" x2="40" y2="42" stroke="#e5e7eb" stroke-width="1"/>
            <line x1="20" y1="51" x2="40" y2="51" stroke="#e5e7eb" stroke-width="1"/>
            <!-- Green check badge -->
            <circle cx="49" cy="11" r="7" fill="#22c55e"/>
            <path d="M45.5 11 L48 13.5 L52.5 8.5" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p class="text-xs text-success font-medium text-center leading-tight">Plano e centralizado</p>
        </div>

        <!-- Card 2: Steep angle -->
        <div class="flex-1 flex flex-col items-center gap-1.5 bg-destructive/10 border border-destructive/30 rounded-xl p-2">
          <svg viewBox="0 0 60 72" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto">
            <!-- Camera frame -->
            <rect x="2" y="2" width="56" height="68" rx="3" fill="#f3f4f6" stroke="#d1d5db" stroke-width="1"/>
            <!-- Skewed ticket (parallelogram) -->
            <polygon points="26,12 44,8 34,64 16,68" fill="white" stroke="#6b7280" stroke-width="1.5"/>
            <!-- Skewed lines -->
            <line x1="19" y1="32" x2="38" y2="27" stroke="#e5e7eb" stroke-width="1"/>
            <line x1="18" y1="43" x2="37" y2="38" stroke="#e5e7eb" stroke-width="1"/>
            <line x1="17" y1="54" x2="36" y2="49" stroke="#e5e7eb" stroke-width="1"/>
            <!-- Red X badge -->
            <circle cx="49" cy="11" r="7" fill="#ef4444"/>
            <path d="M45.5 8L52.5 14M52.5 8L45.5 14" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <p class="text-xs text-destructive font-medium text-center leading-tight">Evite ângulos</p>
        </div>

        <!-- Card 3: Obstruction -->
        <div class="flex-1 flex flex-col items-center gap-1.5 bg-destructive/10 border border-destructive/30 rounded-xl p-2">
          <svg viewBox="0 0 60 72" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto">
            <!-- Camera frame -->
            <rect x="2" y="2" width="56" height="68" rx="3" fill="#f3f4f6" stroke="#d1d5db" stroke-width="1"/>
            <!-- Ticket -->
            <rect x="14" y="11" width="32" height="50" rx="2" fill="white" stroke="#6b7280" stroke-width="1.5"/>
            <!-- Grid lines -->
            <line x1="18" y1="24" x2="42" y2="24" stroke="#e5e7eb" stroke-width="1"/>
            <line x1="18" y1="33" x2="42" y2="33" stroke="#e5e7eb" stroke-width="1"/>
            <line x1="18" y1="42" x2="42" y2="42" stroke="#e5e7eb" stroke-width="1"/>
            <line x1="18" y1="51" x2="42" y2="51" stroke="#e5e7eb" stroke-width="1"/>
            <!-- Finger / thumb overlapping the ticket -->
            <ellipse cx="30" cy="50" rx="13" ry="20" fill="#d4a27a" stroke="#b8865c" stroke-width="1"/>
            <!-- Red X badge -->
            <circle cx="49" cy="11" r="7" fill="#ef4444"/>
            <path d="M45.5 8L52.5 14M52.5 8L45.5 14" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <p class="text-xs text-destructive font-medium text-center leading-tight">Sem obstruções</p>
        </div>
      </div>
    </div>

    <TicketScanner @confirm="handleConfirm" />
  </div>
</template>
