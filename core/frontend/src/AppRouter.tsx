import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { DashboardPage } from '@/pages/DashboardPage'
import { MarketplacePage } from '@/pages/MarketplacePage'
import { SettingsPage } from '@/pages/SettingsPage'

/**
 * Application router.
 *
 * PLUGIN LOADER HOOK — Phase 2:
 * Module routes will be injected here dynamically using React.lazy()
 * and the module's entry_frontend field from the registry.
 * Pattern: <Route path="/modules/:moduleId/*" element={<ModuleHost />} />
 */
export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="marketplace" element={<MarketplacePage />} />
          <Route path="settings" element={<SettingsPage />} />
          {/* Phase 2: <Route path="modules/:moduleId/*" element={<ModuleHost />} /> */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
