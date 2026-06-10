import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface DevModeState {
  developerMode: boolean
  toggleDeveloperMode: () => void
  setDeveloperMode: (enabled: boolean) => void
}

export const useDevModeStore = create<DevModeState>()(
  persist(
    (set) => ({
      developerMode: false,
      toggleDeveloperMode: () => set((s) => ({ developerMode: !s.developerMode })),
      setDeveloperMode: (enabled) => set({ developerMode: enabled }),
    }),
    { name: 'techforge-devmode' }
  )
)
