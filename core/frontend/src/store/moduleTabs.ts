import { create } from 'zustand'

export interface ModuleTab {
  id: string
  name: string
}

interface ModuleTabsState {
  tabs: ModuleTab[]
  activeId: string | null
  stripOpen: boolean
  /** Abre (ou reativa) uma aba de módulo. Idempotente — chamar de novo com o
   * mesmo id só troca qual aba está ativa. */
  openTab: (id: string, name: string) => void
  /** Fecha uma aba. Retorna o novo activeId (pra quem chamou navegar até lá),
   * ou null se não sobrou nenhuma aba aberta. */
  closeTab: (id: string) => string | null
  setActive: (id: string) => void
  /** Alterna a barra de abas — 100% manual, só quem clica no breadcrumb
   * abre ou fecha (nunca abre nem trava fechada sozinha). */
  toggleStrip: () => 'opened' | 'closed'
}

// Módulos abertos ficam montados o tempo todo (ModuleWorkspace) — trocar de
// aba nunca desmonta/remonta a UI do módulo, só esconde via CSS. Abrir ou
// fechar a barra é decisão exclusiva do usuário (botão no breadcrumb),
// nunca automática.
export const useModuleTabsStore = create<ModuleTabsState>((set, get) => ({
  tabs: [],
  activeId: null,
  stripOpen: false,

  openTab: (id, name) => set((s) => {
    const exists = s.tabs.some((t) => t.id === id)
    const tabs = exists ? s.tabs.map((t) => (t.id === id ? { ...t, name } : t)) : [...s.tabs, { id, name }]
    return { tabs, activeId: id }
  }),

  closeTab: (id) => {
    const s = get()
    const idx = s.tabs.findIndex((t) => t.id === id)
    if (idx === -1) return s.activeId

    const tabs = s.tabs.filter((t) => t.id !== id)
    let activeId = s.activeId
    if (s.activeId === id) {
      const next = tabs[idx] ?? tabs[idx - 1]
      activeId = next ? next.id : null
    }
    set({ tabs, activeId })
    return activeId
  },

  setActive: (id) => set({ activeId: id }),

  toggleStrip: () => {
    const stripOpen = !get().stripOpen
    set({ stripOpen })
    return stripOpen ? 'opened' : 'closed'
  },
}))
