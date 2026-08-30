/**
 * Sidebar — Phase 4 / §7.1
 * =========================
 * Renders the complete navigation hierarchy automatically from the backend
 * navigation tree (GET /api/v1/registry/navigation).
 *
 * Structure:
 *   ── Static Core items (Dashboard, Módulos)
 *   ── Installed modules grouped by Category → Vendor → Module
 *      Sorted by module.order (asc) within each vendor group
 *   ── Static Platform items (Marketplace, Configurações)
 *
 * The module never configures its own nav — it only provides manifest metadata.
 * The Core owns all navigation composition (§7.1 restriction).
 */
import { useEffect, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Store, Settings, Puzzle, Boxes, BookOpen,
  ChevronRight, ChevronDown, type LucideIcon,

  // Module icon palette — all kebab-case names mapped to components
  ShieldCheck, Database, Cloud, Server, HardDrive, Activity,
  BarChart, Box, Cpu, Globe, Layers, Lock, Monitor,
  Network, Package, Zap, FileText, Folder, Search,
  Terminal, Wrench, AlertCircle, Archive, Blocks,
} from 'lucide-react'
import { useAppStore } from '@/store/app'
import { useNavStore } from '@/store/nav'
import { cn } from '@/lib/utils'
import type { NavModuleNode } from '@/types'

// ── Icon registry — all lucide names a module may declare ─────────────────────
const ICON_MAP: Record<string, LucideIcon> = {
  // Core nav
  'layout-dashboard': LayoutDashboard,
  'boxes':            Boxes,
  'store':            Store,
  'settings':         Settings,
  'puzzle':           Puzzle,
  // Module icons
  'shield-check':     ShieldCheck,
  'database':         Database,
  'cloud':            Cloud,
  'server':           Server,
  'hard-drive':       HardDrive,
  'activity':         Activity,
  'bar-chart':        BarChart,
  'box':              Box,
  'cpu':              Cpu,
  'globe':            Globe,
  'layers':           Layers,
  'lock':             Lock,
  'monitor':          Monitor,
  'network':          Network,
  'package':          Package,
  'zap':              Zap,
  'file-text':        FileText,
  'folder':           Folder,
  'search':           Search,
  'terminal':         Terminal,
  'wrench':           Wrench,
  'alert-circle':     AlertCircle,
  'archive':          Archive,
  'blocks':           Blocks,
}

// Color map — manifest color → CSS accent class
const COLOR_DOT: Record<string, string> = {
  blue:   'bg-blue-400',
  green:  'bg-green-400',
  red:    'bg-red-400',
  yellow: 'bg-yellow-400',
  orange: 'bg-orange-400',
  purple: 'bg-purple-400',
  pink:   'bg-pink-400',
  cyan:   'bg-cyan-400',
  teal:   'bg-teal-400',
  indigo: 'bg-indigo-400',
  gray:   'bg-gray-400',
}

function ModuleIcon({ name, size = 14 }: { name: string; size?: number }) {
  const Icon = ICON_MAP[name] ?? Puzzle
  return <Icon size={size} />
}

// ── Static nav item ───────────────────────────────────────────────────────────
interface StaticItem {
  id:    string
  label: string
  icon:  LucideIcon
  path:  string
}

function StaticNavItem({ item, collapsed }: { item: StaticItem; collapsed: boolean }) {
  const Icon = item.icon
  return (
    <NavLink
      to={item.path}
      title={collapsed ? item.label : undefined}
      className={({ isActive }) => cn(
        'flex items-center gap-2.5 rounded px-2 py-1.5 text-sm transition-colors select-none',
        'hover:bg-[hsl(var(--bg-subtle))]',
        isActive
          ? 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))] font-medium'
          : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
        collapsed && 'justify-center px-0',
      )}
    >
      <span className="flex-shrink-0 flex items-center justify-center w-5">
        <Icon size={15} />
      </span>
      {!collapsed && <span className="truncate leading-none">{item.label}</span>}
    </NavLink>
  )
}

// ── Module leaf item ──────────────────────────────────────────────────────────
function ModuleNavItem({ mod, collapsed }: { mod: NavModuleNode; collapsed: boolean }) {
  const dotClass = mod.color ? (COLOR_DOT[mod.color] ?? 'bg-[hsl(var(--accent))]') : 'bg-[hsl(var(--accent))]'

  return (
    <NavLink
      to={mod.path}
      title={collapsed ? mod.name : undefined}
      className={({ isActive }) => cn(
        'flex items-center gap-2 rounded px-2 py-1.5 text-xs transition-colors select-none',
        'hover:bg-[hsl(var(--bg-subtle))]',
        isActive
          ? 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))] font-medium'
          : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
        collapsed && 'justify-center px-0',
      )}
    >
      {collapsed ? (
        <span className="flex-shrink-0 flex items-center justify-center w-5">
          <ModuleIcon name={mod.icon} size={14} />
        </span>
      ) : (
        <>
          <span className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0 ml-0.5', dotClass)} />
          <span className="truncate leading-none flex-1">{mod.name}</span>
        </>
      )}
    </NavLink>
  )
}

// ── Vendor group — collapsible ────────────────────────────────────────────────
function VendorGroup({
  vendor, modules, collapsed,
}: { vendor: string; modules: NavModuleNode[]; collapsed: boolean }) {
  const location = useLocation()
  const isAnyActive = modules.some(m => location.pathname.startsWith(m.path))
  const [open, setOpen] = useState(isAnyActive)

  if (collapsed) {
    // In collapsed mode render module icons directly without vendor label
    return (
      <div className="space-y-0.5">
        {modules.map(m => <ModuleNavItem key={m.module_id} mod={m} collapsed />)}
      </div>
    )
  }

  return (
    <div>
      <button
        onClick={() => setOpen(o => !o)}
        className={cn(
          'w-full flex items-center justify-between px-2 py-1 rounded text-xs transition-colors',
          'text-[hsl(var(--text-subtle))] hover:text-[hsl(var(--text-muted))] hover:bg-[hsl(var(--bg-subtle))]',
          isAnyActive && 'text-[hsl(var(--text-muted))]',
        )}
      >
        <span className="truncate font-medium">{vendor}</span>
        {open
          ? <ChevronDown size={11} />
          : <ChevronRight size={11} />}
      </button>

      {open && (
        <div className="mt-0.5 ml-2 pl-2 border-l border-[hsl(var(--border-subtle))] space-y-0.5">
          {modules.map(m => <ModuleNavItem key={m.module_id} mod={m} collapsed={false} />)}
        </div>
      )}
    </div>
  )
}

// ── Category section — collapsible ────────────────────────────────────────────
function CategorySection({
  category, vendors, totalModules, collapsed,
}: {
  category: string
  vendors: { vendor: string; modules: NavModuleNode[] }[]
  totalModules: number
  collapsed: boolean
}) {
  const location = useLocation()
  const isAnyActive = vendors.some(v => v.modules.some(m => location.pathname.startsWith(m.path)))
  const [open, setOpen] = useState(true)   // categories default-open

  if (collapsed) {
    return (
      <div className="space-y-0.5">
        {vendors.map(v => (
          <VendorGroup key={v.vendor} vendor={v.vendor} modules={v.modules} collapsed />
        ))}
      </div>
    )
  }

  return (
    <div>
      <button
        onClick={() => setOpen(o => !o)}
        className={cn(
          'w-full flex items-center justify-between mb-1 px-2 py-0.5 rounded transition-colors',
          'hover:bg-[hsl(var(--bg-subtle))]',
        )}
      >
        <p className={cn(
          'text-[10px] font-medium uppercase tracking-widest',
          isAnyActive ? 'text-[hsl(var(--text-muted))]' : 'text-[hsl(var(--text-subtle))]',
        )}>
          {category}
        </p>
        <span className="flex items-center gap-1">
          <span className="text-[9px] font-mono text-[hsl(var(--text-subtle))]">{totalModules}</span>
          {open ? <ChevronDown size={10} className="text-[hsl(var(--text-subtle))]" /> : <ChevronRight size={10} className="text-[hsl(var(--text-subtle))]" />}
        </span>
      </button>

      {open && (
        <div className="space-y-1">
          {vendors.map(v => (
            <VendorGroup key={v.vendor} vendor={v.vendor} modules={v.modules} collapsed={false} />
          ))}
        </div>
      )}
    </div>
  )
}

// ── Section label ─────────────────────────────────────────────────────────────
function SectionLabel({ label, collapsed }: { label: string; collapsed: boolean }) {
  if (collapsed) return null
  return (
    <p className="mb-1 px-2 text-[10px] font-medium uppercase tracking-widest text-[hsl(var(--text-subtle))]">
      {label}
    </p>
  )
}

// ── Main Sidebar ──────────────────────────────────────────────────────────────
export function Sidebar() {
  const collapsed = useAppStore(s => s.sidebarCollapsed)
  const { tree, refresh } = useNavStore()

  // Fetch navigation tree on mount — `refresh` (zustand action) é estável entre renders
  useEffect(() => { refresh() }, [refresh])

  const CORE_ITEMS: StaticItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/' },
    { id: 'modules',   label: 'Módulos',   icon: Boxes,           path: '/modules' },
    { id: 'dev-center', label: 'Developer Center', icon: BookOpen,   path: '/developer-center' },
  ]

  const PLATFORM_ITEMS: StaticItem[] = [
    { id: 'marketplace',  label: 'Marketplace',   icon: Store,    path: '/marketplace' },
    { id: 'diagnostics',  label: 'Diagnostics',   icon: Activity, path: '/diagnostics' },
    { id: 'settings',     label: 'Configurações', icon: Settings, path: '/settings'   },
  ]

  return (
    <aside className={cn(
      'flex flex-col flex-shrink-0',
      'bg-[hsl(var(--bg-elevated))] border-r border-[hsl(var(--border-subtle))]',
      'sidebar-transition overflow-hidden',
      collapsed
        ? 'w-[var(--sidebar-collapsed-width)]'
        : 'w-[var(--sidebar-width)]',
    )}>

      {/* Logo */}
      <div className={cn(
        'flex items-center h-[var(--header-height)] flex-shrink-0 px-3',
        'border-b border-[hsl(var(--border-subtle))]',
        collapsed ? 'justify-center' : 'gap-2.5',
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

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden py-2 px-1.5 space-y-4">

        {/* Core */}
        <div className="space-y-0.5">
          {CORE_ITEMS.map(item => (
            <StaticNavItem key={item.id} item={item} collapsed={collapsed} />
          ))}
        </div>

        {/* Dynamic module tree — auto-built from registry */}
        {tree && tree.total_modules > 0 && (
          <div className="space-y-3">
            {tree.categories.map(cat => (
              <CategorySection
                key={cat.category}
                category={cat.category}
                vendors={cat.vendors}
                totalModules={cat.total_modules}
                collapsed={collapsed}
              />
            ))}
          </div>
        )}

        {/* Empty state — no modules installed yet */}
        {(!tree || tree.total_modules === 0) && !collapsed && (
          <div>
            <SectionLabel label="Módulos" collapsed={false} />
            <p className="px-2 py-1 text-xs text-[hsl(var(--text-subtle))] italic">
              Nenhum módulo ativo
            </p>
          </div>
        )}

        {/* Platform */}
        <div>
          <SectionLabel label="Plataforma" collapsed={collapsed} />
          <div className="space-y-0.5">
            {PLATFORM_ITEMS.map(item => (
              <StaticNavItem key={item.id} item={item} collapsed={collapsed} />
            ))}
          </div>
        </div>

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
