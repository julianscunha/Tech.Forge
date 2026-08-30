import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { DashboardPage }       from '@/pages/DashboardPage'
import { ModulesPage }         from '@/pages/ModulesPage'
import { MarketplacePage }     from '@/pages/MarketplacePage'
import { SettingsPage }        from '@/pages/SettingsPage'
import { DeveloperCenterPage } from '@/pages/DeveloperCenterPage'
import { DiagnosticsPage }     from '@/pages/DiagnosticsPage'
import { ModuleRouteSync }    from '@/components/modules/ModuleRouteSync'

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
    </BrowserRouter>
  )
}
