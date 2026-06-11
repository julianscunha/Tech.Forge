/**
 * useNavStore
 * ===========
 * Fetches the auto-generated navigation tree from the backend and makes it
 * available to the Sidebar. Re-fetches automatically after Marketplace
 * operations that change the installed module set.
 *
 * Usage:
 *   const { tree, refresh } = useNavStore()
 *   // After install/remove:
 *   useNavStore.getState().refresh()
 */
import { create } from 'zustand'
import { navigationApi } from '@/lib/api'
import type { NavigationTree } from '@/types'

interface NavState {
  tree:    NavigationTree | null
  loading: boolean
  error:   string | null
  refresh: () => Promise<void>
}

export const useNavStore = create<NavState>((set) => ({
  tree:    null,
  loading: false,
  error:   null,

  refresh: async () => {
    set({ loading: true, error: null })
    try {
      const tree = await navigationApi.getTree()
      set({ tree, loading: false })
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Navigation fetch failed',
        loading: false,
      })
    }
  },
}))
