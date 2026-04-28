<script setup lang="ts">
useHead({ title: 'Scan ticket – Lotofácil' })

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
  <div>
    <div class="flex items-center justify-between mb-4">
      <NuxtLink to="/play/my-draw" class="text-sm text-blue-600 hover:underline">
        ← My Draw
      </NuxtLink>
    </div>

    <h1 class="text-2xl font-bold mb-1">Scan Ticket</h1>
    <p class="text-sm text-gray-500 mb-6">
      Point your camera at a filled Lotofácil ticket. The app will read the marked numbers
      automatically.
    </p>

    <TicketScanner @confirm="handleConfirm" />
  </div>
</template>
