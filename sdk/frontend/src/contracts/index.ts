/**
 * TechForge Frontend Module Contract
 * =====================================
 * Every module frontend must export a `moduleConfig` object conforming
 * to ModulePageConfig. The Core uses this to:
 *   - Register the module route
 *   - Show the correct title, icon, and category in the sidebar
 *   - Build breadcrumbs automatically
 *   - Display metadata in the Modules page
 *
 * Usage in frontend/index.tsx:
 *
 *   export const moduleConfig: ModulePageConfig = {
 *     moduleId:    "my_module",
 *     title:       "My Module",
 *     icon:        "Boxes",
 *     category:    "Backup",
 *     vendor:      "ACME Corp",
 *     route:       "/modules/my_module",
 *     description: "Does useful things.",
 *   }
 *
 *   export default function MyModulePage() { ... }
 */

// ── Module page config ────────────────────────────────────────────────────────

export interface ModulePageConfig {
  /** Must match the id in manifest.yaml */
  moduleId: string

  /** Display name shown in breadcrumbs and page title */
  title: string

  /**
   * Lucide icon name shown in sidebar and module card.
   * Must be a valid export from lucide-react.
   * @see https://lucide.dev/icons
   */
  icon: string

  /** Category name — must match a registered Core category */
  category: string

  /** Vendor / company name */
  vendor: string

  /** Route path where the module is mounted */
  route: string

  /** Short description shown in the Modules registry page */
  description?: string

  /**
   * Optional sub-routes within the module.
   * The Plugin Loader registers these under /modules/:moduleId/*
   */
  subRoutes?: ModuleSubRoute[]
}

export interface ModuleSubRoute {
  path:   string
  title:  string
  hidden?: boolean   // if true, shown in content but not in sidebar
}

// ── Lifecycle hooks ───────────────────────────────────────────────────────────

/**
 * Optional lifecycle hooks exported from the module frontend.
 * The Plugin Loader calls these at mount/unmount time.
 *
 * Export them from frontend/index.tsx alongside the default component:
 *   export function onMount()   { ... }
 *   export function onUnmount() { ... }
 */
export interface ModuleLifecycleHooks {
  onMount?:   () => void | Promise<void>
  onUnmount?: () => void | Promise<void>
}

// ── Type guard ────────────────────────────────────────────────────────────────

export function isModulePageConfig(value: unknown): value is ModulePageConfig {
  if (!value || typeof value !== 'object') return false
  const v = value as Record<string, unknown>
  return (
    typeof v.moduleId    === 'string' &&
    typeof v.title       === 'string' &&
    typeof v.icon        === 'string' &&
    typeof v.category    === 'string' &&
    typeof v.vendor      === 'string' &&
    typeof v.route       === 'string'
  )
}
