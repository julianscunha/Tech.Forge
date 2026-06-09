import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { Breadcrumb } from './Breadcrumb'
import { cn } from '@/lib/utils'

export function AppShell() {
  return (
    <div className="flex h-full w-full overflow-hidden bg-[hsl(var(--bg))]">
      {/* Sidebar — 5% UI constraint per spec */}
      <Sidebar />

      {/* Main column */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Header />
        <Breadcrumb />

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
