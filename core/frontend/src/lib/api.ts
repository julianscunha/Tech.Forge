import type { PlatformStatus, Category, Module } from '@/types'

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
  get: (slug: string) => request<Category>(`/categories/${slug}`),
}

// ── Modules ───────────────────────────────────────────────────────────────────

export const modulesApi = {
  list: () => request<Module[]>('/modules'),
  get: (moduleId: string) => request<Module>(`/modules/${moduleId}`),
}

// ── Module Registry (Phase 2) ─────────────────────────────────────────────────

import type { ModuleEntry, RegistrySummary, LoaderResult } from '@/types'

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

import type { PackageInfo, OperationResponse, OperationLogEntry } from '@/types'

export const marketplaceApi = {
  installed:  () => request<PackageInfo[]>('/marketplace/installed'),
  available:  () => request<PackageInfo[]>('/marketplace/available'),
  updates:    () => request<PackageInfo[]>('/marketplace/updates'),

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
      method: 'POST',
      headers: {},   // let browser set multipart boundary
      body: form,
    })
  },

  log: (limit = 50) =>
    request<OperationLogEntry[]>(`/marketplace/log?limit=${limit}`),
}

// ── Navigation Tree (§7.1) ────────────────────────────────────────────────────

import type { NavigationTree } from '@/types'

export const navigationApi = {
  getTree: () => request<NavigationTree>('/registry/navigation'),
}
