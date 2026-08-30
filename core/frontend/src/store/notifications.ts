// Notifications store — Fase 2 Notification Foundation.
// Lightweight polling (30s) + refresh on window focus; no websockets by design
// (spec: "evitar sistemas complexos").
import { create } from 'zustand'
import type { Notification } from '@/types'

interface NotificationsState {
  items: Notification[]
  unreadCount: number
  loading: boolean
  fetchAll: () => Promise<void>
  markRead: (id: number) => Promise<void>
  markAllRead: () => Promise<void>
}

const POLL_INTERVAL_MS = 30_000

export const useNotificationsStore = create<NotificationsState>()((set, get) => ({
  items: [],
  unreadCount: 0,
  loading: false,

  fetchAll: async () => {
    // Só não-lidas — uma vez lida, a notificação sai da lista em vez de
    // ficar acumulando indefinidamente no sino.
    set({ loading: true })
    try {
      const [items, unread] = await Promise.all([
        fetch('/api/v1/notifications?unread_only=true&limit=50').then((r) => r.json()),
        fetch('/api/v1/notifications/unread-count').then((r) => r.json()),
      ])
      set({ items, unreadCount: unread.count })
    } finally {
      set({ loading: false })
    }
  },

  markRead: async (id) => {
    await fetch(`/api/v1/notifications/${id}/read`, { method: 'POST' })
    const item = get().items.find((n) => n.id === id)
    if (item && !item.read) {
      set({
        items: get().items.filter((n) => n.id !== id),
        unreadCount: Math.max(0, get().unreadCount - 1),
      })
    }
  },

  markAllRead: async () => {
    await fetch('/api/v1/notifications/read-all', { method: 'POST' })
    set({ items: [], unreadCount: 0 })
  },
}))

let pollTimer: ReturnType<typeof setInterval> | null = null

/** Start polling + focus refresh. Idempotent — safe to call from the Header mount. */
export function startNotificationsPolling(): void {
  const { fetchAll } = useNotificationsStore.getState()
  void fetchAll()
  if (pollTimer) return
  pollTimer = setInterval(() => void useNotificationsStore.getState().fetchAll(), POLL_INTERVAL_MS)
  window.addEventListener('focus', () => void useNotificationsStore.getState().fetchAll())
}
