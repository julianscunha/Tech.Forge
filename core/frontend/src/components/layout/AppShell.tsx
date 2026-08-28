import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Minimize2 } from 'lucide-react'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { Breadcrumb } from './Breadcrumb'
import { HelpDrawer } from '@/components/help/ContextualHelp'
import { useFocusModeStore } from '@/store/focusMode'
import { cn } from '@/lib/utils'

// context_id por rota — help contextual (Fase 5 §13); mapping em docs/context-map.yaml
const CONTEXT_BY_PATH: [RegExp, string][] = [
  [/^\/$/, 'dashboard'],
  [/^\/dashboard/, 'dashboard'],
  [/^\/modules\/?$/, 'modules'],
  [/^\/marketplace/, 'marketplace'],
  [/^\/developer-center/, 'developer-center'],
  [/^\/settings/, 'settings'],
]

function contextFor(pathname: string): string | undefined {
  for (const [re, id] of CONTEXT_BY_PATH) {
    if (re.test(pathname)) return id
  }
  return undefined
}

export function AppShell() {
  const location = useLocation()
  const contextId = contextFor(location.pathname)
  const { focusMode, setFocusMode } = useFocusModeStore()

  // Focus Mode é escopado ao workspace de um módulo — sair da rota limpa o estado.
  useEffect(() => {
    if (!/^\/modules\//.test(location.pathname)) setFocusMode(false)
  }, [location.pathname, setFocusMode])

  return (
    <div className="flex h-full w-full overflow-hidden bg-[hsl(var(--bg))]">
      {/* Sidebar — 5% UI constraint per spec — recolhida em Focus Mode (Fase 9 §12) */}
      {!focusMode && <Sidebar />}

      {/* Main column */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {focusMode ? (
          <button
            onClick={() => setFocusMode(false)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 text-xs',
              'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
              'border-b border-[hsl(var(--border-subtle))]',
            )}
          >
            <Minimize2 size={12} /> Sair do Focus Mode
          </button>
        ) : (
          <>
            <Header />
            <div className={cn('flex items-center justify-between pr-3')}>
              <Breadcrumb />
              {contextId && <HelpDrawer contextId={contextId} />}
            </div>
          </>
        )}

        {/*
          MODULE RENDER AREA — 95% of usable space
          In Phase 2, the Plugin Loader will render module frontends
          inside this <main> using dynamic imports.
        */}
        <main
          className={cn(
            'flex-1 overflow-y-auto overflow-x-hidden',
            'bg-[hsl(var(--bg))]'
          )}
        >
          <div className="h-full animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
