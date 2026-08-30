import { useEffect, useRef, useState } from 'react'
import { Bell, Check, CheckCheck, Info, AlertTriangle, XCircle, CheckCircle2 } from 'lucide-react'
import {
  useNotificationsStore,
  startNotificationsPolling,
} from '@/store/notifications'
import type { NotificationLevel } from '@/types'
import { cn, formatDateTime } from '@/lib/utils'
import { useTimezoneStore } from '@/store/timezone'

const LEVEL_META: Record<NotificationLevel, { icon: typeof Info; color: string }> = {
  info:    { icon: Info,           color: 'text-[hsl(var(--info,#3b82f6))]' },
  warning: { icon: AlertTriangle,  color: 'text-amber-500' },
  error:   { icon: XCircle,        color: 'text-red-500' },
  success: { icon: CheckCircle2,   color: 'text-emerald-500' },
}

export function NotificationBell() {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const { items, unreadCount, fetchAll, markRead, markAllRead } = useNotificationsStore()
  const timezone = useTimezoneStore((s) => s.timezone)

  useEffect(() => {
    startNotificationsPolling()
  }, [])

  // close on outside click
  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => {
          setOpen((v) => !v)
          if (!open) void fetchAll()
        }}
        aria-label={`Notificações${unreadCount ? ` (${unreadCount} não lidas)` : ''}`}
        className={cn(
          'relative flex items-center justify-center w-7 h-7 rounded',
          'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
          'hover:bg-[hsl(var(--bg-subtle))] transition-colors',
          open && 'bg-[hsl(var(--bg-subtle))] text-[hsl(var(--text))]'
        )}
      >
        <Bell size={14} />
        {unreadCount > 0 && (
          <span
            data-testid="unread-badge"
            className={cn(
              'absolute -top-0.5 -right-0.5 min-w-[14px] h-[14px] px-[3px]',
              'flex items-center justify-center rounded-full text-[9px] font-semibold leading-none',
              'bg-red-500 text-white'
            )}
          >
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div
          className={cn(
            'absolute right-0 top-full mt-1.5 w-80 max-h-96 flex flex-col',
            'rounded-md border border-[hsl(var(--border-subtle))]',
            'bg-[hsl(var(--bg-elevated))] shadow-lg z-50'
          )}
        >
          <div className="flex items-center justify-between px-3 py-2 border-b border-[hsl(var(--border-subtle))]">
            <span className="text-xs font-medium text-[hsl(var(--text-muted))]">
              Notificações
            </span>
            <button
              onClick={() => void markAllRead()}
              disabled={unreadCount === 0}
              aria-label="Marcar todas como lidas"
              className={cn(
                'flex items-center gap-1 text-[11px] px-1.5 py-0.5 rounded transition-colors',
                unreadCount > 0
                  ? 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] hover:bg-[hsl(var(--bg-subtle))]'
                  : 'text-[hsl(var(--text-subtle))] cursor-default'
              )}
            >
              <CheckCheck size={12} /> Marcar todas
            </button>
          </div>

          <div className="overflow-y-auto">
            {items.length === 0 ? (
              <p className="px-3 py-6 text-center text-xs text-[hsl(var(--text-subtle))]">
                Nenhuma notificação.
              </p>
            ) : (
              items.map((n) => {
                const meta = LEVEL_META[n.level]
                const Icon = meta.icon
                return (
                  // Lista mostra só não-lidas — marcar como lida remove o
                  // item daqui (evita acumular indefinidamente no sino).
                  <button
                    key={n.id}
                    onClick={() => void markRead(n.id)}
                    className={cn(
                      'w-full text-left flex gap-2 px-3 py-2 border-b border-[hsl(var(--border-subtle))] last:border-b-0',
                      'hover:bg-[hsl(var(--bg-subtle))] transition-colors bg-[hsl(var(--bg-subtle))]/40'
                    )}
                  >
                    <Icon size={13} className={cn('mt-0.5 flex-shrink-0', meta.color)} />
                    <span className="flex-1 min-w-0">
                      <span className="block text-xs font-medium truncate">{n.title}</span>
                      {n.message && (
                        <span className="block text-[11px] text-[hsl(var(--text-muted))] line-clamp-2">
                          {n.message}
                        </span>
                      )}
                      <span className="block text-[10px] text-[hsl(var(--text-subtle))] mt-0.5">
                        {formatDateTime(n.created_at, timezone)}
                      </span>
                    </span>
                    <Check size={11} className="mt-1 flex-shrink-0 text-[hsl(var(--text-subtle))]" aria-label="Marcar como lida" />
                  </button>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}
