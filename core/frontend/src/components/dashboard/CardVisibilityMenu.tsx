import { useEffect, useRef, useState } from 'react'
import { Settings2 } from 'lucide-react'
import { DASHBOARD_CARD_IDS, useDashboardLayoutStore, type DashboardCardId } from '@/store/dashboardLayout'
import { cn } from '@/lib/utils'

const CARD_LABELS: Record<DashboardCardId, string> = {
  'modules-installed':     'Módulos Instalados',
  'modules-active':        'Módulos Ativos',
  'categories':            'Categorias',
  'services-active':       'Serviços Ativos',
  'module-failures':       'Module Failures',
  'blocked-dependencies':  'Blocked Dependencies',
  'recent-events':         'Recent Critical Events',
  'resource-usage':        'Recursos (CPU/mem/disco)',
  'heaviest-module':       'Módulo mais pesado',
}

export function CardVisibilityMenu() {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const { hidden, toggleVisible } = useDashboardLayoutStore()

  useEffect(() => {
    if (!open) return
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [open])

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label="Personalizar cards da Dashboard"
        title="Personalizar cards"
        className={cn(
          'flex items-center justify-center w-7 h-7 rounded',
          'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
          'hover:bg-[hsl(var(--bg-subtle))] transition-colors',
        )}
      >
        <Settings2 size={14} />
      </button>

      {open && (
        <div
          className={cn(
            'absolute right-0 top-full mt-1.5 z-30 w-64',
            'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border-subtle))]',
            'rounded-lg shadow-lg p-2',
          )}
        >
          <p className="text-[10px] uppercase tracking-wide text-[hsl(var(--text-subtle))] px-2 py-1">
            Mostrar cards
          </p>
          {DASHBOARD_CARD_IDS.map((id) => (
            <label
              key={id}
              className="flex items-center gap-2 px-2 py-1.5 rounded text-xs cursor-pointer hover:bg-[hsl(var(--bg-subtle))]"
            >
              <input
                type="checkbox"
                checked={!hidden.includes(id)}
                onChange={() => toggleVisible(id)}
                className="rounded"
              />
              <span className="text-[hsl(var(--text))]">{CARD_LABELS[id]}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  )
}
