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
  safe_mode: boolean
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

export type ModuleStatus = 'INSTALLED' | 'DISABLED' | 'INVALID' | 'INCOMPATIBLE' | 'BLOCKED'

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

// ── Dependency Governance (Fase 8.1) ──────────────────────────────────────────

export type DependencyStatus =
  | 'SATISFIED' | 'MISSING' | 'INCOMPATIBLE_VERSION' | 'DISABLED'
  | 'CONFLICT' | 'CYCLIC' | 'OPTIONAL_UNAVAILABLE'

// ── Module Runtime (Fase 9) ────────────────────────────────────────────────────

export type RuntimeState = 'READY' | 'INITIALIZING' | 'EXECUTING' | 'DEGRADED' | 'FAILED' | 'STOPPED'

export interface ModuleRuntimeEntry {
  module_id: string
  state: RuntimeState
  last_error: string | null
  last_execution: string | null
  uptime_seconds: number | null
}

export interface Dependency {
  target_type: 'module' | 'capability'
  target_id: string
  version_range: string | null
  required: boolean
  status: DependencyStatus | null
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
export type TrustLevel = 'TRUSTED' | 'VERIFIED' | 'UNVERIFIED' | 'MODIFIED' | 'INVALID'

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
  is_enabled?: boolean | null
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

// ── Catalog (Fase 11) ───────────────────────────────────────────────────────
// Espelha exatamente app/api/routes/catalog.py::CatalogModuleRead e afins —
// não reusa PackageInfo (Fase 4) porque os dois já divergiram em nomes de
// campo (ex: compatibility aqui é o .value do enum, não o objeto completo).

export type CatalogSourceType = 'local' | 'official_catalog' | 'custom_catalog'

export interface CatalogModule {
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
  trust_level: TrustLevel
  is_installed: boolean
  installed_version: string | null
  install_date: string | null
  has_update: boolean
  source: CatalogSourceType
  source_url: string | null
  signature: string | null
  checksum: string | null
  publisher: string | null
  icon: string | null
  color: string | null
  homepage: string | null
  documentation: string | null
  favorite: boolean
}

export interface CatalogModuleListResponse {
  items: CatalogModule[]
  total: number
  page: number
  page_size: number
  conflicts: Record<string, string[]>
}

export interface CatalogCategory {
  name: string
  count: number
}

export interface CatalogSourceConfig {
  id: string
  name: string
  url: string
  type: CatalogSourceType
  enabled: boolean
  status: 'available' | 'unavailable'
}

export type InstallJobPhase = 'ACQUIRING' | 'VALIDATING' | 'INSTALLING' | 'DONE' | 'FAILED'

export interface InstallJob {
  job_id: string
  module_id: string
  phase: InstallJobPhase
  error: string | null
  started_at: string
  finished_at: string | null
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
  capabilities: string[]
}

// ── Fase 8 — Service Registry ───────────────────────────────────────────────

export type ServiceStatus = 'REGISTERED' | 'ACTIVE' | 'UNAVAILABLE' | 'DISABLED' | 'FAILED' | 'REMOVED'

export interface ServiceDescriptor {
  service_id:      string
  module_id:       string
  module_version:  string
  service_version: string
  capabilities:    string[]
  status:          ServiceStatus
  contract:        ServiceContract | null
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

// ── Module Trust (Fase 10) ─────────────────────────────────────────────────

export interface PublisherRead {
  id:           string
  name:         string
  type:         string
  public_key:   string | null
  trust_status: string
  extra:        Record<string, unknown> | null
  created_at:   string
}

export interface ModuleTrust {
  module_id:        string
  trust_level:      TrustLevel
  integrity_status: string
  signature_status: string
  publisher:        PublisherRead | null
}

// ── Configuration & Persistence (Fase 12) ───────────────────────────────────

export interface ModuleConfigField {
  id: string
  type: 'string' | 'integer' | 'float' | 'boolean'
  default: unknown
}

export interface ModuleConfigResponse {
  module_id: string
  values: Record<string, unknown>
}

export interface StorageStatus {
  database: boolean
  writable: boolean
}

export interface MigrationsStatus {
  head: string | null
  current: string | null
  up_to_date: boolean
}

export type PlatformConfig = Record<string, unknown>

// ── Fase 14 — Observability / Diagnostics ────────────────────────────────────

export interface DiagnosticError {
  id: number
  source: string
  code: string | null
  message: string
  detail: string | null
  module_id: string | null
  execution_id: string | null
  created_at: string | null
}

export interface ExecutionEntry {
  execution_id: string
  module_id: string
  status: string
  duration_seconds: number
  error_summary?: string | null
  created_at: string | null
}

export interface ResourceUsage {
  cpu_percent: number
  memory_rss_bytes: number
  disk_used_bytes: number
  disk_total_bytes: number
}

export interface HeaviestModule {
  module_id: string
  disk_bytes: number
  avg_duration_seconds: number
  execution_count: number
  failure_rate: number
}

export interface DependencyCheck {
  name: string
  passed: boolean
  required: boolean
  detail: string
}

export interface DiagnosticsHealth {
  platform: {
    name: string
    version: string
    database_status: string
    modules_installed: number
    modules_enabled: number
    categories_registered: number
  }
  storage: { database: boolean; writable: boolean }
  runtime: {
    state: string
    started_at: string | null
    uptime_seconds: number | null
    frontend_mode: string
    components: Record<string, boolean>
    events: { timestamp: string; name: string; detail: string }[]
  }
}
