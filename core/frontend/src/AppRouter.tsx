import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { DashboardPage }       from '@/pages/DashboardPage'
import { ModuleRouteSync }    from '@/components/modules/ModuleRouteSync'

// Rotas fora do landing (index) carregadas sob demanda — evita empacotar
// mermaid/cytoscape/katex (usados só por DeveloperCenterPage/Diagnostics)
// no bundle inicial. Achado em revisão de performance: chunk único de
// 1.1MB/286KB gzip sem code-splitting nenhum (budget: 200KB gzip).
const ModulesPage         = lazy(() => import('@/pages/ModulesPage').then(m => ({ default: m.ModulesPage })))
const MarketplacePage     = lazy(() => import('@/pages/MarketplacePage').then(m => ({ default: m.MarketplacePage })))
const SettingsPage        = lazy(() => import('@/pages/SettingsPage').then(m => ({ default: m.SettingsPage })))
const DeveloperCenterPage = lazy(() => import('@/pages/DeveloperCenterPage').then(m => ({ default: m.DeveloperCenterPage })))
const DiagnosticsPage     = lazy(() => import('@/pages/DiagnosticsPage').then(m => ({ default: m.DiagnosticsPage })))

function RouteFallback() {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <p className="text-sm text-[hsl(var(--text-subtle))]">Carregando…</p>
    </div>
  )
}

/**
 * Application Router — Phase 5
 *
 * PLUGIN LOADER HOOK (Phase 2+):
 * `/modules/:moduleId/*` só sincroniza a URL com a aba ativa
 * (ModuleRouteSync) — o host de verdade (ModuleHost) é renderizado por
 * ModuleWorkspace, uma instância por aba aberta, persistente entre rotas.
 */
export function AppRouter() {
  return (
    <BrowserRouter>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index                   element={<DashboardPage />} />
            <Route path="modules"          element={<ModulesPage />} />
            <Route path="marketplace"      element={<MarketplacePage />} />
            <Route path="developer-center" element={<DeveloperCenterPage />} />
            <Route path="diagnostics"      element={<DiagnosticsPage />} />
            <Route path="settings"         element={<SettingsPage />} />
            {/* Phase 2+ — Plugin Loader: sincroniza URL <-> aba de módulo.
                O conteúdo em si vem de ModuleWorkspace (montado em AppShell,
                persistente entre trocas de rota — ver store/moduleTabs). */}
            <Route path="modules/:moduleId/*" element={<ModuleRouteSync />} />
            <Route path="*"                element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
