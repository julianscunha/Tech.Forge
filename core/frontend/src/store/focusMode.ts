import { create } from 'zustand'

interface FocusModeState {
  focusMode: boolean
  toggleFocusMode: () => void
  setFocusMode: (enabled: boolean) => void
}

// Fase 9 §12 — Focus Mode: recolhe sidebar/topbar, maximiza o workspace do
// módulo. Deliberadamente não persistido (zustand/persist) — é um estado de
// sessão de leitura do módulo atual, não uma preferência duradoura.
export const useFocusModeStore = create<FocusModeState>((set) => ({
  focusMode: false,
  toggleFocusMode: () => set((s) => ({ focusMode: !s.focusMode })),
  setFocusMode: (enabled) => set({ focusMode: enabled }),
}))
