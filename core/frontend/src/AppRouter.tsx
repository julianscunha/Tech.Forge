import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { DashboardPage } from '@/pages/DashboardPage'
import { ModulesPage } from '@/pages/ModulesPage'
import { MarketplacePage } from '@/pages/MarketplacePage'
import { SettingsPage } from '@/pages/SettingsPage'

/**
 * Application router.
 *
 * PLUGIN LOADER HOOK — Phase 2+:
 * When a module is enabled, the Plugin Loader injects a route here:
 *   <Route path="/modules/:moduleId/*" element={<ModuleHost moduleId={...} />} />
 * ModuleHost uses React.lazy() to import the module's entry_frontend dynamically.
 */
export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="modules" element={<ModulesPage />} />
          {/* Phase 2+: <Route path="modules/:moduleId/*" element={<ModuleHost />} /> */}
          <Route path="marketplace" element={<MarketplacePage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
