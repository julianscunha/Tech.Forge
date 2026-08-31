import { useLocation, Link } from 'react-router-dom'
import { ChevronRight, ChevronDown } from 'lucide-react'
import { isModuleRoute } from '@/lib/moduleRoute'
import { useModuleTabsStore } from '@/store/moduleTabs'
import { cn } from '@/lib/utils'

const PATH_LABELS: Record<string, string> = {
  '':           'Dashboard',
  'modules':    'Módulos',
  'marketplace': 'Marketplace',
  'settings':   'Configurações',
  'developer-center': 'Developer Center',
}

export function Breadcrumb() {
  const { pathname } = useLocation()
  const segments = pathname.split('/').filter(Boolean)
  const { tabs, activeId, stripOpen, toggleStrip } = useModuleTabsStore()

  const onModuleRoute = isModuleRoute(pathname)
  const activeTabName = tabs.find((t) => t.id === activeId)?.name

  const crumbs = [
    { label: 'TechForge', to: '/' },
    ...segments.map((seg, i) => ({
      label: onModuleRoute && i === segments.length - 1 ? (activeTabName ?? seg) : (PATH_LABELS[seg] ?? seg),
      to: '/' + segments.slice(0, i + 1).join('/'),
    })),
  ]

  return (
    <nav aria-label="breadcrumb" className="flex items-center gap-1 min-w-0 overflow-hidden whitespace-nowrap relative">
      {crumbs.map((crumb, i) => {
        const isLast = i === crumbs.length - 1
        const showTabToggle = isLast && onModuleRoute && tabs.length > 0

        return (
          <span key={crumb.to} className="flex items-center gap-1">
            {i > 0 && <ChevronRight size={11} className="text-[hsl(var(--text-subtle))] flex-shrink-0" />}
            {showTabToggle ? (
              <button
                onClick={toggleStrip}
                aria-expanded={stripOpen}
                title="Mostrar/ocultar módulos abertos"
                className={cn(
                  'flex items-center gap-1 -my-1 py-1 px-1.5 rounded',
                  'text-xs font-medium text-[hsl(var(--text))]',
                  'hover:bg-[hsl(var(--bg-subtle))] transition-colors',
                )}
              >
                <span className="truncate">{crumb.label}</span>
                <ChevronDown
                  size={11}
                  className={cn('text-[hsl(var(--text-subtle))] transition-transform', stripOpen && 'rotate-180')}
                />
              </button>
            ) : isLast ? (
              <span className="text-xs text-[hsl(var(--text))] font-medium truncate">{crumb.label}</span>
            ) : (
              <Link
                to={crumb.to}
                className="text-xs text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] transition-colors"
              >
                {crumb.label}
              </Link>
            )}
          </span>
        )
      })}
    </nav>
  )
}
