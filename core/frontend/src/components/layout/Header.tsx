import { PanelLeft, Sun, Moon } from 'lucide-react'
import { useAppStore } from '@/store/app'
import { NotificationBell } from '@/components/layout/NotificationBell'
import { cn } from '@/lib/utils'

export function Header() {
  const { theme, toggleTheme, toggleSidebar, sidebarCollapsed } = useAppStore()

  return (
    <header
      className={cn(
        'flex items-center justify-between',
        'px-3 h-[var(--header-height)]',
        'border-b border-[hsl(var(--border-subtle))]',
        'bg-[hsl(var(--bg-elevated))]',
        'z-20 flex-shrink-0'
      )}
    >
      {/* Left: sidebar toggle */}
      <div className="flex items-center gap-2">
        <button
          onClick={toggleSidebar}
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className={cn(
            'flex items-center justify-center w-7 h-7 rounded',
            'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
            'hover:bg-[hsl(var(--bg-subtle))] transition-colors'
          )}
        >
          <PanelLeft size={15} />
        </button>

        <span className="text-xs font-mono text-[hsl(var(--text-subtle))] select-none hidden sm:block">
          TechForge
        </span>
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-1">
        {/* Notifications */}
        <NotificationBell />

        {/* Theme toggle */}
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
