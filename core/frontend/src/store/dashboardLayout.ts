import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const DASHBOARD_CARD_IDS = [
  'modules-installed', 'modules-active', 'categories', 'services-active',
  'module-failures', 'blocked-dependencies', 'recent-events',
  'resource-usage', 'heaviest-module',
] as const

export type DashboardCardId = typeof DASHBOARD_CARD_IDS[number]

interface DashboardLayoutState {
  order: DashboardCardId[]
  hidden: DashboardCardId[]
  moveCard: (dragId: DashboardCardId, dropId: DashboardCardId) => void
  toggleVisible: (id: DashboardCardId) => void
}

export const useDashboardLayoutStore = create<DashboardLayoutState>()(
  persist(
    (set, get) => ({
      order: [...DASHBOARD_CARD_IDS],
      hidden: [],

      moveCard: (dragId, dropId) => {
        if (dragId === dropId) return
        const order = [...get().order]
        const from = order.indexOf(dragId)
        const to = order.indexOf(dropId)
        if (from === -1 || to === -1) return
        order.splice(from, 1)
        order.splice(to, 0, dragId)
        set({ order })
      },

      toggleVisible: (id) => {
        const current = get().hidden
        const hidden = current.includes(id) ? current.filter((h) => h !== id) : [...current, id]
        set({ hidden })
      },
    }),
    { name: 'techforge-dashboard-layout' }
  )
)

/** Ordem efetiva: cards persistidos primeiro, seguidos de qualquer card
 * novo (adicionado numa versão futura) que ainda não esteja na ordem
 * salva do usuário — evita que um card novo simplesmente desapareça. */
export function getEffectiveOrder(order: DashboardCardId[]): DashboardCardId[] {
  const missing = DASHBOARD_CARD_IDS.filter((id) => !order.includes(id))
  return [...order.filter((id) => DASHBOARD_CARD_IDS.includes(id)), ...missing]
}
