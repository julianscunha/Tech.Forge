import type { NavSection } from '@/types'

/**
 * Static Core navigation.
 *
 * In Phase 2, the Plugin Loader will call `registerModuleNavItem()`
 * to inject module entries into the "modules" section below.
 * This keeps navigation extensible without modifying this file.
 */
export const CORE_NAV: NavSection[] = [
  {
    id: 'core',
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: 'LayoutDashboard', path: '/' },
    ],
  },
  {
    id: 'platform',
    label: 'Plataforma',
    items: [
      { id: 'marketplace', label: 'Marketplace', icon: 'Store', path: '/marketplace' },
      { id: 'settings', label: 'Configurações', icon: 'Settings', path: '/settings' },
    ],
  },
  {
    /**
     * PLUGIN LOADER HOOK — Phase 2
     * This section will be populated dynamically when modules are loaded.
     * Each enabled module contributes one NavItem here via Plugin Loader.
     */
    id: 'modules',
    label: 'Módulos',
    items: [],  // injected at runtime by Plugin Loader
  },
]
