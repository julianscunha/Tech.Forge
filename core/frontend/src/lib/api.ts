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
