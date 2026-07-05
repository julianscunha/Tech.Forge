import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { DashboardPage }       from '@/pages/DashboardPage'
import { ModulesPage }         from '@/pages/ModulesPage'
import { MarketplacePage }     from '@/pages/MarketplacePage'
import { SettingsPage }        from '@/pages/SettingsPage'
import { DeveloperCenterPage } from '@/pages/DeveloperCenterPage'

/**
 * Application Router — Phase 5
 *
 * PLUGIN LOADER HOOK (Phase 2+):
 * When a module is enabled the Plugin Loader injects:
 *   <Route path="/modules/:moduleId/*" element={<ModuleHost />} />
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
          <Route path="settings"         element={<SettingsPage />} />
          {/* Phase 2+: <Route path="modules/:moduleId/*" element={<ModuleHost />} /> */}
          <Route path="*"                element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
