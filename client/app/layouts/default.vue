<script setup lang="ts">
const route = useRoute()

const mode = computed<'research' | 'play' | 'admin'>(() => {
  if (route.path.startsWith('/play')) return 'play'
  if (route.path.startsWith('/admin')) return 'admin'
  return 'research'
})
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50 text-gray-900">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200 shadow-sm">
      <div class="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <NuxtLink to="/" class="text-xl font-bold tracking-tight hover:text-blue-600 transition-colors">
          Lotofácil Research
        </NuxtLink>

        <!-- Mode indicator -->
        <nav class="flex items-center gap-2">
          <NuxtLink
            to="/research"
            class="px-4 py-1.5 rounded-full text-sm font-medium transition-colors"
            :class="mode === 'research'
              ? 'bg-blue-100 text-blue-800'
              : 'text-gray-500 hover:bg-gray-100'"
          >
            Research
          </NuxtLink>
          <NuxtLink
            to="/play"
            class="px-4 py-1.5 rounded-full text-sm font-medium transition-colors"
            :class="mode === 'play'
              ? 'bg-purple-100 text-purple-800'
              : 'text-gray-500 hover:bg-gray-100'"
          >
            Play
          </NuxtLink>
          <NuxtLink
            to="/admin"
            class="px-4 py-1.5 rounded-full text-sm font-medium transition-colors"
            :class="mode === 'admin'
              ? 'bg-gray-200 text-gray-800'
              : 'text-gray-400 hover:bg-gray-100'"
          >
            Admin
          </NuxtLink>
        </nav>
      </div>
    </header>

    <!-- Research / entertainment disclaimer (always visible) -->
    <div class="bg-amber-50 border-b border-amber-200 px-4 py-2 text-center text-xs text-amber-800">
      For research and entertainment purposes only. Statistical analysis does not predict future
      lottery results. Play responsibly.
    </div>

    <!-- Main content -->
    <main class="flex-1 max-w-6xl mx-auto w-full px-4 py-6">
      <slot />
    </main>

    <!-- Footer -->
    <footer class="border-t border-gray-200 bg-white py-4 text-center text-xs text-gray-400">
      Lotofácil Research Tool — not affiliated with Caixa Econômica Federal.
    </footer>
  </div>
</template>
