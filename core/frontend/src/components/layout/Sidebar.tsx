import { useLocation, NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Store, Settings, Puzzle, Boxes,
  ChevronRight, type LucideIcon,
} from 'lucide-react'
import { useAppStore } from '@/store/app'
import { CORE_NAV } from '@/lib/navigation'
import { cn } from '@/lib/utils'
import type { NavItem } from '@/types'

const ICON_MAP: Record<string, LucideIcon> = {
  LayoutDashboard,
  Store,
  Settings,
  Puzzle,
  Boxes,
}

function NavIcon({ name, size = 15 }: { name: string; size?: number }) {
  const Icon = ICON_MAP[name] ?? Puzzle
  return <Icon size={size} />
}

function SidebarItem({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
  return (
    <NavLink
      to={item.path}
      title={collapsed ? item.label : undefined}
      className={({ isActive }) =>
        cn(
          'group flex items-center gap-2.5 rounded px-2 py-1.5',
          'text-sm transition-colors select-none',
          'hover:bg-[hsl(var(--bg-subtle))]',
          isActive
            ? 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))] font-medium'
            : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
          collapsed ? 'justify-center px-0' : ''
        )
      }
    >
      <span className="flex-shrink-0 flex items-center justify-center w-5">
        <NavIcon name={item.icon} size={15} />
      </span>
      {!collapsed && <span className="truncate leading-none">{item.label}</span>}
      {!collapsed && item.badge !== undefined && (
        <span className="ml-auto flex h-4 min-w-4 items-center justify-center rounded-full
          bg-[hsl(var(--accent-muted))] px-1 text-[10px] font-medium text-[hsl(var(--accent))]">
          {item.badge}
        </span>
      )}
    </NavLink>
  )
}

export function Sidebar() {
  const collapsed = useAppStore((s) => s.sidebarCollapsed)
  const location = useLocation()
  void location

  return (
    <aside
      className={cn(
        'flex flex-col flex-shrink-0',
        'bg-[hsl(var(--bg-elevated))] border-r border-[hsl(var(--border-subtle))]',
        'sidebar-transition overflow-hidden',
        collapsed
          ? 'w-[var(--sidebar-collapsed-width)]'
          : 'w-[var(--sidebar-width)]'
      )}
    >
      {/* Logo */}
      <div className={cn(
        'flex items-center h-[var(--header-height)] flex-shrink-0',
        'border-b border-[hsl(var(--border-subtle))] px-3',
        collapsed ? 'justify-center' : 'gap-2.5'
      )}>
        <div className="w-6 h-6 rounded-md bg-[hsl(var(--accent))] flex items-center justify-center flex-shrink-0">
          <ChevronRight size={12} className="text-white" strokeWidth={2.5} />
        </div>
        {!collapsed && (
          <span className="font-semibold text-sm tracking-tight text-[hsl(var(--text))]">
            TechForge
          </span>
        )}
      </div>

      {/* Nav sections */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden py-2 px-1.5 space-y-4">
        {CORE_NAV.map((section) => (
          <div key={section.id}>
            {!collapsed && section.label && (
              <p className="mb-1 px-2 text-[10px] font-medium uppercase tracking-widest text-[hsl(var(--text-subtle))]">
                {section.label}
              </p>
            )}
            {section.items.length > 0 ? (
              <div className="space-y-0.5">
                {section.items.map((item) => (
                  <SidebarItem key={item.id} item={item} collapsed={collapsed} />
                ))}
              </div>
            ) : (
              !collapsed && section.id === 'modules-installed' && (
                <p className="px-2 py-1 text-xs text-[hsl(var(--text-subtle))] italic">
                  Nenhum módulo ativo
                </p>
              )
            )}
          </div>
        ))}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="px-3 py-2 border-t border-[hsl(var(--border-subtle))]">
          <p className="text-[10px] font-mono text-[hsl(var(--text-subtle))]">v1.0.0</p>
        </div>
      )}
    </aside>
  )
}
