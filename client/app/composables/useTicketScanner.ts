import type { ScannedTicket } from '~/types/api'

export type ScannerStatus = 'idle' | 'loading' | 'success' | 'error'

export function useTicketScanner() {
  const stream = ref<MediaStream | null>(null)
  const status = ref<ScannerStatus>('idle')
  const error = ref<string | null>(null)
  const result = ref<ScannedTicket | null>(null)
  const permissionDenied = ref(false)

  // ── Camera lifecycle ─────────────────────────────────────────────────────

  async function startCamera(): Promise<void> {
    error.value = null
    permissionDenied.value = false
    try {
      stream.value = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
      })
    } catch (err) {
      const name = err instanceof Error ? err.name : ''
      if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
        permissionDenied.value = true
      } else {
        error.value = 'Could not access the camera. Please check your browser permissions.'
      }
    }
  }

  function stopCamera(): void {
    if (!stream.value) return
    stream.value.getTracks().forEach((track) => track.stop())
    stream.value = null
  }

  // ── Frame capture + compression ──────────────────────────────────────────

  async function captureFrame(videoEl: HTMLVideoElement): Promise<Blob | null> {
    const videoW = videoEl.videoWidth
    const videoH = videoEl.videoHeight
    if (!videoW || !videoH) return null

    const MAX = 1280
    const ratio = Math.min(MAX / videoW, MAX / videoH, 1)
    const w = Math.round(videoW * ratio)
    const h = Math.round(videoH * ratio)

    const canvas = document.createElement('canvas')
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    if (!ctx) return null
    ctx.drawImage(videoEl, 0, 0, w, h)

    return new Promise<Blob | null>((resolve) => {
      canvas.toBlob((blob) => resolve(blob), 'image/jpeg', 0.85)
    })
  }

  // ── Upload ───────────────────────────────────────────────────────────────

  async function uploadImage(blob: Blob): Promise<void> {
    status.value = 'loading'
    error.value = null
    result.value = null

    const config = useRuntimeConfig()
    const baseURL = config.public.apiBase as string

    const form = new FormData()
    form.append('image', blob, 'ticket.jpg')

    try {
      const data = await $fetch<ScannedTicket>(`${baseURL}/v1/tickets/scan`, {
        method: 'POST',
        body: form,
        onResponseError({ response }) {
          const body = response._data as { error?: { message?: string } } | undefined
          const msg = body?.error?.message ?? `HTTP ${response.status}`
          throw new Error(msg)
        },
      })
      result.value = data
      status.value = 'success'
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'An unexpected error occurred.'
      status.value = 'error'
    }
  }

  // ── Reset ────────────────────────────────────────────────────────────────

  function reset(): void {
    status.value = 'idle'
    error.value = null
    result.value = null
    permissionDenied.value = false
  }

  onUnmounted(() => {
    stopCamera()
  })

  return {
    stream: readonly(stream),
    status: readonly(status),
    error: readonly(error),
    result: readonly(result),
    permissionDenied: readonly(permissionDenied),
    startCamera,
    stopCamera,
    captureFrame,
    uploadImage,
    reset,
  }
}
