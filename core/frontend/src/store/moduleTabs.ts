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
  /** Alterna a barra de abas. Retorna 'blocked' se havia mais de uma aba
   * aberta e a barra estava tentando fechar — nesse caso nada muda, quem
   * chamou decide como avisar o usuário. */
  toggleStrip: () => 'opened' | 'closed' | 'blocked'
}

// Módulos abertos ficam montados o tempo todo (ModuleWorkspace) — trocar de
// aba nunca desmonta/remonta a UI do módulo, só esconde via CSS. A barra só
// pode ficar fechada com 0 ou 1 aba aberta (invariante reforçada tanto aqui
// quanto no toggle manual).
export const useModuleTabsStore = create<ModuleTabsState>((set, get) => ({
  tabs: [],
  activeId: null,
  stripOpen: false,

  openTab: (id, name) => set((s) => {
    const exists = s.tabs.some((t) => t.id === id)
    const tabs = exists ? s.tabs.map((t) => (t.id === id ? { ...t, name } : t)) : [...s.tabs, { id, name }]
    return { tabs, activeId: id, stripOpen: s.stripOpen || tabs.length > 1 }
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
    const s = get()
    if (s.stripOpen && s.tabs.length > 1) return 'blocked'
    const stripOpen = !s.stripOpen
    set({ stripOpen })
    return stripOpen ? 'opened' : 'closed'
  },
}))
