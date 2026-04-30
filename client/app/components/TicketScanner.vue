<script setup lang="ts">
const emit = defineEmits<{
  confirm: [numbers: number[]]
}>()

const { stream, status, error, result, permissionDenied, startCamera, stopCamera, captureFrame, uploadImage, reset } =
  useTicketScanner()

// Internal view state: 'capture' | 'preview' | 'loading' | 'result'
type ViewState = 'capture' | 'preview' | 'loading' | 'result'
const view = ref<ViewState>('capture')

const videoRef = ref<HTMLVideoElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)

// Editable copy of the scanned games (for the result view)
const editableGames = ref<number[][]>([])

// Preview state (between capture and upload)
const capturedBlob = ref<Blob | null>(null)
const previewUrl = ref<string | null>(null)

onMounted(async () => {
  await startCamera()
})

// Bind stream to <video> once both are ready
watch(
  [stream, videoRef],
  ([s, v]) => {
    if (s && v) {
      v.srcObject = s
    }
  },
  { immediate: true },
)

// Sync status → view
watch(status, (s) => {
  if (s === 'loading') {
    view.value = 'loading'
  } else if (s === 'success' && result.value) {
    // Deep-copy so the user can toggle numbers
    editableGames.value = result.value.games.map((g) => [...g])
    view.value = 'result'
  } else if (s === 'error') {
    view.value = 'capture'
  }
})

// ── Capture ────────────────────────────────────────────────────────────────

async function handleCapture(): Promise<void> {
  if (!videoRef.value) return
  const blob = await captureFrame(videoRef.value)
  if (!blob) return
  stopCamera()
  capturedBlob.value = blob
  previewUrl.value = URL.createObjectURL(blob)
  view.value = 'preview'
}

// ── Preview ────────────────────────────────────────────────────────────────

function revokePreviewUrl(): void {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = null
  }
}

async function handleConfirmPreview(): Promise<void> {
  const blob = capturedBlob.value
  if (!blob) return
  revokePreviewUrl()
  capturedBlob.value = null
  await uploadImage(blob)
}

async function handleRetakeFromPreview(): Promise<void> {
  revokePreviewUrl()
  capturedBlob.value = null
  view.value = 'capture'
  await startCamera()
}

onBeforeUnmount(() => {
  revokePreviewUrl()
})

// ── File fallback ──────────────────────────────────────────────────────────

function handleFileInput(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploadImage(file)
}

// ── Result view helpers ────────────────────────────────────────────────────

function isMarked(gameIdx: number, n: number): boolean {
  return editableGames.value[gameIdx]?.includes(n) ?? false
}

function toggleNumber(gameIdx: number, n: number): void {
  const game = editableGames.value[gameIdx]
  if (!game) return
  const idx = game.indexOf(n)
  if (idx === -1) {
    game.push(n)
    game.sort((a, b) => a - b)
  } else {
    game.splice(idx, 1)
  }
}

function handleSave(): void {
  const first = editableGames.value[0]
  if (!first) return
  emit('confirm', first)
}

async function handleRetake(): Promise<void> {
  reset()
  editableGames.value = []
  view.value = 'capture'
  await startCamera()
}

function handleDiscard(): void {
  reset()
  editableGames.value = []
  view.value = 'capture'
  startCamera()
}

// Numbers 1-25 for the result grid
const ALL_NUMBERS = Array.from({ length: 25 }, (_, i) => i + 1)
</script>

<template>
  <div class="flex flex-col items-center gap-4">
    <!-- ── Capture view ─────────────────────────────────────────────────── -->
    <template v-if="view === 'capture'">
      <!-- Camera preview -->
      <div
        v-if="!permissionDenied"
        class="relative w-full max-w-sm aspect-video bg-black rounded-xl overflow-hidden"
      >
        <video
          ref="videoRef"
          autoplay
          playsinline
          muted
          class="w-full h-full object-cover"
        />
        <!-- Ticket alignment guide overlay — only shown while the camera stream is live -->
        <div
          v-if="view === 'capture'"
          class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
        >
          <!-- Dark vignette around the guide -->
          <div class="absolute inset-0" style="background: rgba(0,0,0,0.35)" />
          <!-- Guide rectangle: portrait ~1:2.3 ratio -->
          <div
            class="relative z-10 flex flex-col items-center justify-end pb-2"
            style="width: 52%; aspect-ratio: 1 / 2.3; border: 2px solid rgba(255,255,255,0.75); border-radius: 4px; box-shadow: 0 0 0 9999px rgba(0,0,0,0.35);"
          >
            <!-- Corner markers -->
            <span class="absolute top-0 left-0 w-3 h-3 border-t-2 border-l-2 border-white rounded-tl-sm" />
            <span class="absolute top-0 right-0 w-3 h-3 border-t-2 border-r-2 border-white rounded-tr-sm" />
            <span class="absolute bottom-0 left-0 w-3 h-3 border-b-2 border-l-2 border-white rounded-bl-sm" />
            <span class="absolute bottom-0 right-0 w-3 h-3 border-b-2 border-r-2 border-white rounded-br-sm" />
          </div>
          <!-- Label below the guide -->
          <p class="relative z-10 mt-2 text-xs text-white/80 font-medium tracking-wide">
            Align ticket within the guide
          </p>
        </div>
      </div>

      <!-- Error banner -->
      <p v-if="error" class="text-sm text-red-600 bg-red-50 rounded-lg px-4 py-2 w-full max-w-sm">
        {{ error }}
      </p>

      <!-- Capture button -->
      <button
        v-if="!permissionDenied"
        type="button"
        class="px-8 py-3 bg-purple-600 text-white font-semibold rounded-lg hover:bg-purple-700 transition-colors"
        @click="handleCapture"
      >
        Capture
      </button>

      <!-- File picker fallback -->
      <div v-if="permissionDenied" class="flex flex-col items-center gap-3 w-full max-w-sm">
        <p class="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 text-center">
          Camera access was denied. You can upload a photo of the ticket instead.
        </p>
        <label
          class="cursor-pointer px-8 py-3 bg-purple-600 text-white font-semibold rounded-lg hover:bg-purple-700 transition-colors"
        >
          Choose photo
          <input
            ref="fileInputRef"
            type="file"
            accept="image/*"
            capture="environment"
            class="sr-only"
            @change="handleFileInput"
          >
        </label>
      </div>
    </template>

    <!-- ── Preview view ─────────────────────────────────────────────────── -->
    <template v-else-if="view === 'preview'">
      <div class="relative w-full max-w-sm aspect-video bg-black rounded-xl overflow-hidden">
        <img
          :src="previewUrl ?? undefined"
          class="w-full h-full object-cover"
          alt="Captured ticket"
        >
      </div>
      <p class="text-sm text-gray-500 text-center">
        Does the ticket look clear and fully visible?
      </p>
      <div class="flex gap-3 w-full max-w-sm">
        <button
          type="button"
          class="flex-1 px-4 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          @click="handleRetakeFromPreview"
        >
          Retake
        </button>
        <button
          type="button"
          class="flex-1 px-4 py-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 transition-colors"
          @click="handleConfirmPreview"
        >
          Confirm
        </button>
      </div>
    </template>

    <!-- ── Loading view ─────────────────────────────────────────────────── -->
    <template v-else-if="view === 'loading'">
      <div class="flex flex-col items-center gap-4 py-10">
        <svg
          class="animate-spin h-10 w-10 text-purple-600"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
        <p class="text-gray-600 font-medium">Analysing ticket…</p>
      </div>
    </template>

    <!-- ── Result view ───────────────────────────────────────────────────── -->
    <template v-else-if="view === 'result'">
      <p class="text-sm text-gray-500 text-center">
        Review the detected numbers. Tap any cell to toggle it on/off.
      </p>

      <div
        v-for="(game, gIdx) in editableGames"
        :key="gIdx"
        class="w-full max-w-sm bg-white border border-gray-200 rounded-xl p-4"
      >
        <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
          Game {{ gIdx + 1 }}
        </p>
        <div class="grid grid-cols-5 gap-1.5">
          <button
            v-for="n in ALL_NUMBERS"
            :key="n"
            type="button"
            :class="[
              'h-10 w-full rounded-lg text-sm font-medium transition-colors',
              isMarked(gIdx, n)
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
            ]"
            @click="toggleNumber(gIdx, n)"
          >
            {{ String(n).padStart(2, '0') }}
          </button>
        </div>
        <p class="mt-2 text-xs text-gray-400 text-right">
          {{ game.length }} marked
        </p>
      </div>

      <div class="flex gap-3 w-full max-w-sm">
        <button
          type="button"
          class="flex-1 px-4 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          @click="handleDiscard"
        >
          Discard
        </button>
        <button
          type="button"
          class="px-4 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          @click="handleRetake"
        >
          Retake
        </button>
        <button
          type="button"
          class="flex-1 px-4 py-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 transition-colors"
          :disabled="!editableGames[0]?.length"
          @click="handleSave"
        >
          Save
        </button>
      </div>
    </template>
  </div>
</template>
