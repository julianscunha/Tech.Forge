// ── Platform ──────────────────────────────────────────────────────────────────

export type NotificationLevel = 'info' | 'warning' | 'error' | 'success'

export interface Notification {
  id: number
  level: NotificationLevel
  title: string
  message?: string | null
  module_id?: string | null
  read: boolean
  created_at: string
}

export interface PlatformStatus {
  platform_name: string
  platform_version: string
  backend_status: 'online' | 'degraded' | 'offline'
  database_status: 'connected' | 'error'
  modules_installed: number
  modules_enabled: number
  categories_registered: number
}

// ── Category ──────────────────────────────────────────────────────────────────

export interface Category {
  id: number
  slug: string
  name: string
  description?: string
  icon?: string
  created_at: string
}

// ── Module ────────────────────────────────────────────────────────────────────

export type ModuleLifecycleState = 'enabled' | 'disabled' | 'error' | 'loading'

export interface Module {
  id: number
  module_id: string
  name: string
  version: string
  description?: string
  vendor?: string
  author?: string
  platform_min_version?: string
  platform_max_version?: string
  entry_backend?: string
  entry_frontend?: string
  is_enabled: boolean
  installed_at: string
  updated_at?: string
  category?: Category
}

// ── Navigation ────────────────────────────────────────────────────────────────

/**
 * Represents a navigation entry in the sidebar.
 * In Phase 2, module entries are dynamically injected here by the Plugin Loader.
 */
export interface NavItem {
  id: string
  label: string
  icon: string
  path: string
  badge?: number
  /** Set to true for items injected by the Plugin Loader */
  isModule?: boolean
  moduleId?: string
  categorySlug?: string
}

export interface NavSection {
  id: string
  label?: string
  items: NavItem[]
}

// ── Theme ─────────────────────────────────────────────────────────────────────

export type Theme = 'light' | 'dark'

// ── Module Engine (Phase 2) ───────────────────────────────────────────────────

export type ModuleStatus = 'INSTALLED' | 'DISABLED' | 'INVALID' | 'INCOMPATIBLE'

export interface ModuleEntry {
  module_id: string
  name: string
  version: string
  category: string
  vendor: string
  author: string
  description: string
  status: ModuleStatus
  install_date: string
  errors: string[]
  warnings: string[]
  platform_min_version: string
  platform_max_version: string
  entry_backend: string | null
  entry_frontend: string | null
  is_active: boolean
  manifest_raw?: Record<string, unknown> | null
}

export interface RegistrySummary {
  total: number
  installed: number
  disabled: number
  invalid: number
  categories: string[]
}

export interface LoadEvent {
  timestamp: string
  module_id: string | null
  level: 'info' | 'warning' | 'error'
  message: string
  details: Record<string, unknown>
}

export interface LoaderResult {
  scanned: number
  installed: number
  disabled: number
  invalid: number
  incompatible: number
  journal: LoadEvent[]
}

// ── Marketplace (Phase 4) ─────────────────────────────────────────────────────

export type CompatibilityLevel = 'compatible' | 'warning' | 'incompatible'
export type TrustLevel = 'verified' | 'community' | 'unsigned' | 'untrusted'

export interface PackageInfo {
  module_id: string
  name: string
  version: string
  category: string
  vendor: string
  author: string
  description: string
  platform_min_version: string
  platform_max_version: string
  compatibility: CompatibilityLevel
  is_installed: boolean
  installed_version: string | null
  install_date: string | null
  trust_level: TrustLevel
  signature: string | null
  checksum: string | null
  publisher: string | null
  icon: string | null
  color: string | null
  order: number | null
  has_update: boolean
  homepage: string | null
  documentation: string | null
}

export interface OperationResponse {
  success: boolean
  status: string
  module_id: string
  message: string
}

export interface OperationLogEntry {
  timestamp: string
  operation: string
  module_id: string
  version: string
  status: string
  message: string
  details: Record<string, unknown>
}

// ── Navigation Tree (§7.1) ────────────────────────────────────────────────────

export interface NavModuleNode {
  module_id: string
  name:      string
  icon:      string
  color:     string | null
  order:     number
  path:      string
  vendor:    string
  category:  string
}

export interface NavVendorNode {
  vendor:  string
  modules: NavModuleNode[]
}

export interface NavCategoryNode {
  category:      string
  total_modules: number
  vendors:       NavVendorNode[]
}

export interface NavigationTree {
  total_modules: number
  categories:    NavCategoryNode[]
}

// ── Documentation Engine (Phase 5) ───────────────────────────────────────────

export interface DocEntryMeta {
  id:        string
  title:     string
  category:  string
  order:     number
  tags:      string[]
  excerpt:   string
  module_id: string | null
}

export interface DocEntryFull extends DocEntryMeta {
  content: string
}

export interface DocSearchResult {
  doc_id:    string
  title:     string
  category:  string
  excerpt:   string
  module_id: string | null
  score:     number
}

export interface ServiceExport {
  name:        string
  description: string
  parameters:  { name: string; type: string; description: string; required: boolean }[]
  returns:     string | null
  examples:    string[]
}

export interface ServiceContract {
  service_id:   string
  module_id:    string
  description:  string
  version:      string
  exports:      ServiceExport[]
  dependencies: string[]
}

export interface DocSummary {
  total_docs:      number
  total_contracts: number
  categories:      Record<string, number>
}

// ── §16 Documentation First Principle — Completeness ──────────────────────────

export interface DoDCheck {
  name:     string
  passed:   boolean
  required: boolean
  detail:   string
}

export interface CompletenessReport {
  module_id:   string
  module_type: string
  is_complete: boolean
  score:       number
  missing:     string[]
  checks:      DoDCheck[]
}
