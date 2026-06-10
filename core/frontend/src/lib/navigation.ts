import type { NavSection } from '@/types'

/**
 * Static Core navigation.
 *
 * PLUGIN LOADER HOOK — Phase 2+:
 * When the registry loads modules with status INSTALLED, the Plugin Loader
 * calls registerModuleNavItem() to inject entries into the 'modules' section.
 * This keeps navigation extensible without modifying this file.
 */
export const CORE_NAV: NavSection[] = [
  {
    id: 'core',
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: 'LayoutDashboard', path: '/' },
      { id: 'modules',   label: 'Módulos',   icon: 'Boxes',           path: '/modules' },
    ],
  },
  {
    id: 'platform',
    label: 'Plataforma',
    items: [
      { id: 'marketplace', label: 'Marketplace',  icon: 'Store',    path: '/marketplace' },
      { id: 'settings',    label: 'Configurações', icon: 'Settings', path: '/settings' },
    ],
  },
  {
    /**
     * PLUGIN LOADER HOOK — Phase 2+
     * Populated at runtime when modules are enabled.
     * Each INSTALLED module contributes one NavItem here.
     */
    id: 'modules-installed',
    label: 'Módulos Ativos',
    items: [],
  },
]
