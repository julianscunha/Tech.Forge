import { create } from 'zustand'

export interface ModuleTab {
  id: string
  name: string
}

export const TAB_SLOT_COUNT = 5

interface ModuleTabsState {
  tabs: ModuleTab[]
  activeId: string | null
  stripOpen: boolean
  /** Slot (1-5) em que cada aba foi aberta — só controla em qual listbox ela
   * aparece na tira de abas; a aba continua montada globalmente
   * (ModuleWorkspace ignora slot, sempre mantém tudo vivo). */
  tabSlot: Record<string, number>
  /** Slot selecionado no listbox à esquerda da tira de abas. */
  activeSlot: number
  /** Abre (ou reativa) uma aba de módulo. Idempotente — chamar de novo com o
   * mesmo id só troca qual aba está ativa. Aba nova entra no `activeSlot`
   * atual; aba já existente puxa o `activeSlot` pro slot onde ela mora (pra
   * o usuário clicar num módulo em qualquer lugar da UI e sempre ver a
   * aba dele aparecer na tira, mesmo se o slot visível era outro). */
  openTab: (id: string, name: string) => void
  /** Fecha uma aba. Retorna o novo activeId (pra quem chamou navegar até lá),
   * ou null se não sobrou nenhuma aba aberta. */
  closeTab: (id: string) => string | null
  setActive: (id: string) => void
  setActiveSlot: (slot: number) => void
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
  tabSlot: {},
  activeSlot: 1,

  openTab: (id, name) => set((s) => {
    const exists = s.tabs.some((t) => t.id === id)
    const tabs = exists ? s.tabs.map((t) => (t.id === id ? { ...t, name } : t)) : [...s.tabs, { id, name }]
    const tabSlot = exists ? s.tabSlot : { ...s.tabSlot, [id]: s.activeSlot }
    const activeSlot = exists ? (s.tabSlot[id] ?? s.activeSlot) : s.activeSlot
    return { tabs, tabSlot, activeId: id, activeSlot }
  }),

  closeTab: (id) => {
    const s = get()
    const idx = s.tabs.findIndex((t) => t.id === id)
    if (idx === -1) return s.activeId

    const tabs = s.tabs.filter((t) => t.id !== id)
    const tabSlot = { ...s.tabSlot }
    delete tabSlot[id]
    let activeId = s.activeId
    if (s.activeId === id) {
      const next = tabs[idx] ?? tabs[idx - 1]
      activeId = next ? next.id : null
    }
    set({ tabs, tabSlot, activeId })
    return activeId
  },

  setActive: (id) => set({ activeId: id }),

  setActiveSlot: (slot) => set({ activeSlot: slot }),

  toggleStrip: () => {
    const stripOpen = !get().stripOpen
    set({ stripOpen })
    return stripOpen ? 'opened' : 'closed'
  },
}))
