// ── Platform ──────────────────────────────────────────────────────────────────

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
