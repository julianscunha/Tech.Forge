import { X, Puzzle } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import { isModuleRoute } from '@/lib/moduleRoute'
import { useModuleTabsStore } from '@/store/moduleTabs'
import { cn } from '@/lib/utils'

/**
 * Barra de abas de módulo — retraída por padrão, aberta pelo botão de
 * breadcrumb (ver Breadcrumb.tsx). Só existe pra dar visibilidade/controle
 * sobre o que `ModuleWorkspace` já mantém montado; fechar uma aba aqui
 * desmonta o módulo de verdade (perde o estado dele).
 */
export function ModuleTabStrip() {
  const location = useLocation()
  const navigate = useNavigate()
  const { tabs, activeId, stripOpen, setActive, closeTab } = useModuleTabsStore()

  if (!isModuleRoute(location.pathname) || tabs.length === 0) return null

  function handleActivate(id: string) {
    setActive(id)
    navigate(`/modules/${id}`)
  }

  function handleClose(e: React.MouseEvent, id: string) {
    e.stopPropagation()
    const nextActiveId = closeTab(id)
    if (location.pathname.startsWith(`/modules/${id}`)) {
      navigate(nextActiveId ? `/modules/${nextActiveId}` : '/modules')
    }
  }

  return (
    <div
      className={cn(
        'flex items-stretch gap-px px-1 flex-shrink-0 overflow-x-auto',
        'bg-[hsl(var(--bg-subtle))] transition-[max-height,opacity] duration-200 ease-out',
        stripOpen
          ? 'max-h-9 opacity-100 border-b border-[hsl(var(--border-subtle))]'
          : 'max-h-0 opacity-0 overflow-hidden',
      )}
    >
      {tabs.map((tab) => {
        const active = tab.id === activeId
        return (
          <div
            key={tab.id}
            role="tab"
            aria-selected={active}
            onClick={() => handleActivate(tab.id)}
            className={cn(
              'relative top-px flex items-center gap-1.5 px-2.5 py-1.5 rounded-t-md text-xs cursor-pointer whitespace-nowrap max-w-[200px] border border-transparent',
              active
                ? 'bg-[hsl(var(--bg))] border-[hsl(var(--border-subtle))] border-b-[hsl(var(--bg))] text-[hsl(var(--text))] font-medium'
                : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
            )}
          >
            <Puzzle size={12} className="flex-shrink-0 opacity-75" />
            <span className="truncate">{tab.name}</span>
            <button
              onClick={(e) => handleClose(e, tab.id)}
              aria-label={`Fechar ${tab.name}`}
              title="Fechar"
              className="flex-shrink-0 flex items-center justify-center w-4 h-4 rounded text-[hsl(var(--text-subtle))] hover:bg-[hsl(var(--border-subtle))] hover:text-[hsl(var(--text))]"
            >
              <X size={11} />
            </button>
          </div>
        )
      })}
    </div>
  )
}
