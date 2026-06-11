export type ActiveGame = 'lotofacil' | 'megasena'

// Singleton ref — shared across all component instances in the same SPA session
const activeGame = ref<ActiveGame>('lotofacil')

export function useActiveGame() {
  function setActiveGame(game: ActiveGame) {
    activeGame.value = game
  }

  return { activeGame: readonly(activeGame), setActiveGame }
}
