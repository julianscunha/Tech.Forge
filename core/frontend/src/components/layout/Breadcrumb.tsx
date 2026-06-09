import { useLocation, Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

const PATH_LABELS: Record<string, string> = {
  '': 'Dashboard',
  'marketplace': 'Marketplace',
  'settings': 'Configurações',
  // Phase 2: module paths will be added dynamically
}

export function Breadcrumb() {
  const { pathname } = useLocation()

  const segments = pathname.split('/').filter(Boolean)
  const crumbs = [
    { label: 'TechForge', to: '/' },
    ...segments.map((seg, i) => ({
      label: PATH_LABELS[seg] ?? seg,
      to: '/' + segments.slice(0, i + 1).join('/'),
    })),
  ]

  return (
    <nav
      aria-label="breadcrumb"
      className="flex items-center gap-1 px-4 h-8 flex-shrink-0 border-b border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg))]"
    >
      {crumbs.map((crumb, i) => {
        const isLast = i === crumbs.length - 1
        return (
          <span key={crumb.to} className="flex items-center gap-1">
            {i > 0 && <ChevronRight size={11} className="text-[hsl(var(--text-subtle))]" />}
            {isLast ? (
              <span className={cn('text-xs text-[hsl(var(--text))] font-medium')}>
                {crumb.label}
              </span>
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
