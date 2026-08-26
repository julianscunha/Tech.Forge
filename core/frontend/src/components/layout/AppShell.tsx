import { Outlet, useLocation } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { Breadcrumb } from './Breadcrumb'
import { HelpDrawer } from '@/components/help/ContextualHelp'
import { cn } from '@/lib/utils'

// context_id por rota — help contextual (Fase 5 §13); mapping em docs/context-map.yaml
const CONTEXT_BY_PATH: [RegExp, string][] = [
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

  return (
    <div className="flex h-full w-full overflow-hidden bg-[hsl(var(--bg))]">
      {/* Sidebar — 5% UI constraint per spec */}
      <Sidebar />

      {/* Main column */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Header />
        <div className={cn('flex items-center justify-between pr-3')}>
          <Breadcrumb />
          {contextId && <HelpDrawer contextId={contextId} />}
        </div>

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
