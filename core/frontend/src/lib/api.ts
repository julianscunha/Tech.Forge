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

  remove: (moduleId: string) =>
    request<OperationResponse>(`/marketplace/remove/${moduleId}`, { method: 'DELETE' }),

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
