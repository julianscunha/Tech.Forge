// All imports must be at the top of the file
import type {
  PlatformStatus,
  Category,
  Module,
  ModuleEntry,
  RegistrySummary,
  LoaderResult,
  PackageInfo,
  OperationResponse,
  OperationLogEntry,
  NavigationTree,
  CatalogModuleListResponse,
  CatalogCategory,
  CatalogModule,
  CatalogSourceConfig,
  InstallJob,
} from '@/types'

const BASE_URL = '/api/v1'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(detail.detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

// ── Platform ──────────────────────────────────────────────────────────────────

export const platformApi = {
  getStatus: () => request<PlatformStatus>('/platform/status'),
}

// ── Categories ────────────────────────────────────────────────────────────────

export const categoriesApi = {
  list: () => request<Category[]>('/categories'),
  get:  (slug: string) => request<Category>(`/categories/${slug}`),
}

// ── Modules (Phase 1 DB) ──────────────────────────────────────────────────────

export const modulesApi = {
  list: () => request<Module[]>('/modules'),
  get:  (moduleId: string) => request<Module>(`/modules/${moduleId}`),
}

// ── Module Registry (Phase 2) ─────────────────────────────────────────────────

export const registryApi = {
  summary: () =>
    request<RegistrySummary>('/registry/summary'),

  listModules: (developerMode = false) =>
    request<ModuleEntry[]>(`/registry/modules?developer_mode=${developerMode}`),

  getModule: (moduleId: string, developerMode = false) =>
    request<ModuleEntry>(`/registry/modules/${moduleId}?developer_mode=${developerMode}`),

  getLoaderJournal: () =>
    request<LoaderResult>('/registry/loader/journal'),
}

// ── Marketplace (Phase 4) ─────────────────────────────────────────────────────

export const marketplaceApi = {
  installed: () => request<PackageInfo[]>('/marketplace/installed'),
  available: () => request<PackageInfo[]>('/marketplace/available'),
  updates:   () => request<PackageInfo[]>('/marketplace/updates'),

  install: (moduleId: string) =>
    request<OperationResponse>(`/marketplace/install/${moduleId}`, { method: 'POST' }),

  remove: (moduleId: string, keepData = false) =>
    request<OperationResponse>(`/marketplace/remove/${moduleId}?keep_data=${keepData}`, { method: 'DELETE' }),

  update: (moduleId: string) =>
    request<OperationResponse>(`/marketplace/update/${moduleId}`, { method: 'POST' }),

  importMod: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<OperationResponse>('/marketplace/import', {
      method:  'POST',
      headers: {},     // let the browser set the multipart boundary
      body:    form,
    })
  },

  log: (limit = 50) =>
    request<OperationLogEntry[]>(`/marketplace/log?limit=${limit}`),

  // ── Lifecycle (Fase 4 §9/§10) ──────────────────────────────────────────────
  activate: (moduleId: string) =>
    request<OperationResponse>(`/marketplace/activate/${moduleId}`, { method: 'POST' }),

  deactivate: (moduleId: string) =>
    request<OperationResponse>(`/marketplace/deactivate/${moduleId}`, { method: 'POST' }),
}

// ── Catalog (Fase 11) ─────────────────────────────────────────────────────────

export interface CatalogListParams {
  search?: string
  category?: string
  source?: string
  trust_level?: string
  compatible_only?: boolean
  installed_only?: boolean
  favorites_only?: boolean
  sort?: 'name' | 'recent'
  page?: number
  page_size?: number
}

function toQueryString(params: object): string {
  const q = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') q.set(key, String(value))
  }
  const s = q.toString()
  return s ? `?${s}` : ''
}

export const catalogApi = {
  list: (params: CatalogListParams = {}) =>
    request<CatalogModuleListResponse>(`/catalog/modules${toQueryString(params)}`),

  categories: () => request<CatalogCategory[]>('/catalog/categories'),

  get: (moduleId: string) => request<CatalogModule>(`/catalog/modules/${moduleId}`),

  updates: (params: { page?: number; page_size?: number } = {}) =>
    request<CatalogModuleListResponse>(`/catalog/updates${toQueryString(params)}`),

  sources: () => request<CatalogSourceConfig[]>('/catalog/sources'),

  addSource: (payload: { name: string; url: string; type: 'official_catalog' | 'custom_catalog' }) =>
    request<CatalogSourceConfig>('/catalog/sources', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  removeSource: (sourceId: string) =>
    request<{ success: boolean }>(`/catalog/sources/${sourceId}`, { method: 'DELETE' }),

  favorites: () => request<string[]>('/catalog/favorites'),

  favorite: (moduleId: string) =>
    request<{ success: boolean }>(`/catalog/favorites/${moduleId}`, { method: 'POST' }),

  unfavorite: (moduleId: string) =>
    request<{ success: boolean }>(`/catalog/favorites/${moduleId}`, { method: 'DELETE' }),
}

// ── Remote installation with progress (Fase 11 Slice 5b) ─────────────────────

export const installJobApi = {
  installRemote: (moduleId: string, sourceId?: string) =>
    request<{ job_id: string }>(`/marketplace/install-remote/${moduleId}`, {
      method: 'POST',
      body: JSON.stringify({ source_id: sourceId ?? null }),
    }),

  getJob: (jobId: string) => request<InstallJob>(`/marketplace/install-jobs/${jobId}`),
}

// ── Navigation Tree (§7.1) ────────────────────────────────────────────────────

export const navigationApi = {
  getTree: () => request<NavigationTree>('/registry/navigation'),
}

// ── Documentation Engine (Phase 5) ───────────────────────────────────────────

import type {
  DocEntryMeta, DocEntryFull, DocSearchResult,
  ServiceContract, DocSummary,
} from '@/types'

export const docsApi = {
  summary:    () => request<DocSummary>('/docs/summary'),
  list:       (category?: string, module_id?: string) => {
    const params = new URLSearchParams()
    if (category)  params.set('category', category)
    if (module_id) params.set('module_id', module_id)
    const q = params.toString()
    return request<DocEntryMeta[]>(`/docs/list${q ? '?' + q : ''}`)
  },
  article:    (docId: string) => request<DocEntryFull>(`/docs/article/${docId}`),
  search:     (q: string, limit = 20) =>
    request<DocSearchResult[]>(`/docs/search?q=${encodeURIComponent(q)}&limit=${limit}`),
  contracts:  () => request<ServiceContract[]>('/docs/contracts'),
  contract:   (moduleId: string) => request<ServiceContract>(`/docs/contracts/${moduleId}`),
  reindex:    () => request<{ indexed: number; contracts: number }>('/docs/reindex', { method: 'POST' }),
  exportAI:   (categories?: string) => {
    const q = categories ? `?categories=${encodeURIComponent(categories)}` : ''
    return fetch(`/api/v1/docs/export/ai-context${q}`).then(r => r.text())
  },
}

// ── §16 Documentation First Principle — Completeness ──────────────────────────

import type { CompletenessReport } from '@/types'

export const completenessApi = {
  all:  () => request<CompletenessReport[]>('/docs/completeness'),
  byModule: (moduleId: string) => request<CompletenessReport>(`/docs/completeness/${moduleId}`),
}

// ── Fase 8 — Service Registry ───────────────────────────────────────────────

import type { ServiceDescriptor } from '@/types'

export const servicesApi = {
  list:         () => request<ServiceDescriptor[]>('/services'),
  get:          (serviceId: string) => request<ServiceDescriptor>(`/services/${serviceId}`),
  capabilities: () => request<Record<string, string[]>>('/services/capabilities'),
}

// ── Fase 8.1 — Dependency Governance ─────────────────────────────────────────

import type { Dependency } from '@/types'

export const dependenciesApi = {
  dependencies: (moduleId: string) => request<Dependency[]>(`/modules/${moduleId}/dependencies`),
  dependents:   (moduleId: string) => request<string[]>(`/modules/${moduleId}/dependents`),
  graph:        () => request<{ mermaid: string }>('/dependencies/graph'),
}

// ── Fase 9 — Module Runtime ───────────────────────────────────────────────────

import type { ModuleRuntimeEntry } from '@/types'

export const runtimeApi = {
  getModule: (moduleId: string) => request<ModuleRuntimeEntry>(`/runtime/modules/${moduleId}`),
}

// ── Fase 10 — Module Trust ────────────────────────────────────────────────

import type { ModuleTrust } from '@/types'

export const moduleTrustApi = {
  list: () => request<ModuleTrust[]>('/modules/trust'),
  get:  (moduleId: string) => request<ModuleTrust>(`/modules/${moduleId}/trust`),
}

// ── Fase 12 — Configuration & Persistence ────────────────────────────────────

import type { ModuleConfigResponse, StorageStatus, MigrationsStatus, PlatformConfig } from '@/types'

export const moduleConfigApi = {
  get: (moduleId: string) => request<ModuleConfigResponse>(`/modules/${moduleId}/config`),
  put: (moduleId: string, values: Record<string, unknown>) =>
    request<ModuleConfigResponse>(`/modules/${moduleId}/config`, {
      method: 'PUT',
      body: JSON.stringify({ values }),
    }),
}

export const systemApi = {
  storageStatus:    () => request<StorageStatus>('/system/storage/status'),
  migrationsStatus: () => request<MigrationsStatus>('/system/migrations/status'),
}

export const platformConfigApi = {
  get: () => request<PlatformConfig>('/config'),
}
