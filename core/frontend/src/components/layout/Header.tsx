import { PanelLeft, Sun, Moon } from 'lucide-react'
import { useAppStore } from '@/store/app'
import { NotificationBell } from '@/components/layout/NotificationBell'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { HelpDrawer } from '@/components/help/ContextualHelp'
import { cn } from '@/lib/utils'

interface HeaderProps {
  contextId?: string
}

export function Header({ contextId }: HeaderProps) {
  const { theme, toggleTheme, toggleSidebar, sidebarCollapsed } = useAppStore()

  return (
    <header
      className={cn(
        'flex items-center gap-2 justify-between',
        'px-3 h-[var(--header-height)]',
        'border-b border-[hsl(var(--border-subtle))]',
        'bg-[hsl(var(--bg-elevated))]',
        'z-20 flex-shrink-0'
      )}
    >
      {/* Left: sidebar toggle + breadcrumb (substitui o rótulo "TechForge" — já é o primeiro item do breadcrumb) */}
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <button
          onClick={toggleSidebar}
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className={cn(
            'flex items-center justify-center w-7 h-7 rounded flex-shrink-0',
            'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
            'hover:bg-[hsl(var(--bg-subtle))] transition-colors'
          )}
        >
          <PanelLeft size={15} />
        </button>

        <Breadcrumb />
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-1 flex-shrink-0">
        {contextId && <HelpDrawer contextId={contextId} />}
        <NotificationBell />

        <button
          onClick={toggleTheme}
          aria-label="Alternar tema"
          className={cn(
            'flex items-center justify-center w-7 h-7 rounded',
            'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
            'hover:bg-[hsl(var(--bg-subtle))] transition-colors'
          )}
        >
          {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
        </button>
      </div>
    </header>
  )
}
