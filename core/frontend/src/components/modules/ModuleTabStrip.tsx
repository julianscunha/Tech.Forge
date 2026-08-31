import { useEffect, useRef, useState } from 'react'
import { X, Puzzle } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import { isModuleRoute } from '@/lib/moduleRoute'
import { TAB_SLOT_COUNT, useModuleTabsStore } from '@/store/moduleTabs'
import { cn } from '@/lib/utils'

const SLOT_NUMBERS = Array.from({ length: TAB_SLOT_COUNT }, (_, i) => i + 1)

/** Botão compacto — só o número do slot ativo. Clique abre um popover pra
 * escolher entre 1 e 5, sem ocupar espaço permanente na tira de abas. */
function SlotPicker({ activeSlot, onSelect }: { activeSlot: number; onSelect: (slot: number) => void }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [open])

  return (
    <div className="relative flex-shrink-0" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        title="Escolher slot de abas"
        className={cn(
          'flex items-center justify-center w-6 h-6 my-1.5 ml-1 rounded-md text-[11px] font-semibold transition-colors',
          'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))]',
          'hover:brightness-110',
        )}
      >
        {activeSlot}
      </button>

      {open && (
        <div
          role="listbox"
          aria-label="Slot de abas"
          className={cn(
            'absolute left-0 top-full mt-1 z-30 flex flex-col gap-0.5 p-1',
            'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border-subtle))]',
            'rounded-lg shadow-lg',
          )}
        >
          {SLOT_NUMBERS.map((slot) => (
            <button
              key={slot}
              role="option"
              aria-selected={slot === activeSlot}
              onClick={() => { onSelect(slot); setOpen(false) }}
              className={cn(
                'flex items-center justify-center w-6 h-6 rounded text-[11px] font-medium transition-colors',
                slot === activeSlot
                  ? 'bg-[hsl(var(--accent))] text-white'
                  : 'text-[hsl(var(--text-muted))] hover:bg-[hsl(var(--bg-subtle))] hover:text-[hsl(var(--text))]',
              )}
            >
              {slot}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

/**
 * Barra de abas de módulo — retraída por padrão, só abre/fecha quando o
 * usuário clica no botão de breadcrumb (ver Breadcrumb.tsx). Puramente
 * manual, sem abertura automática. Existe pra dar visibilidade/controle
 * sobre o que `ModuleWorkspace` já mantém montado; fechar uma aba aqui
 * desmonta o módulo de verdade (perde o estado dele).
 *
 * Botão de slot (1-5) na lateral esquerda: cada número é um agrupamento
 * independente de listagem — a aba fica "guardada" no slot em que foi
 * aberta, então trocar de slot não fecha nem desmonta nada, só filtra o
 * que aparece aqui.
 */
export function ModuleTabStrip() {
  const location = useLocation()
  const navigate = useNavigate()
  const { tabs, activeId, stripOpen, tabSlot, activeSlot, setActive, setActiveSlot, closeTab } = useModuleTabsStore()

  if (!isModuleRoute(location.pathname) || tabs.length === 0) return null

  const visibleTabs = tabs.filter((tab) => (tabSlot[tab.id] ?? 1) === activeSlot)

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
        'flex items-stretch flex-shrink-0',
        'bg-[hsl(var(--bg-subtle))] transition-[max-height,opacity] duration-200 ease-out',
        stripOpen
          ? 'max-h-9 opacity-100 border-b border-[hsl(var(--border-subtle))]'
          : 'max-h-0 opacity-0 overflow-hidden',
      )}
    >
      <SlotPicker activeSlot={activeSlot} onSelect={setActiveSlot} />
      <div className="w-px my-1.5 mx-1 bg-[hsl(var(--border-subtle))] flex-shrink-0" />
      <div className="flex items-stretch gap-px px-1 overflow-x-auto overflow-y-hidden">
        {visibleTabs.map((tab) => {
          const active = tab.id === activeId
          return (
            <div
              key={tab.id}
              role="tab"
              aria-selected={active}
              onClick={() => handleActivate(tab.id)}
              className={cn(
                'relative top-px flex items-center gap-1.5 pl-2.5 pr-1.5 py-1.5 rounded-t-md text-xs cursor-pointer whitespace-nowrap max-w-[200px]',
                active
                  ? 'bg-[hsl(var(--bg))] text-[hsl(var(--text))] font-medium'
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
    </div>
  )
}
