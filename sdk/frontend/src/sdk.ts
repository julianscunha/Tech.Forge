/**
 * TechForge SDK — Frontend Service Implementations
 * ==================================================
 * Phase 3: fully-typed service stubs with clear Phase 4 upgrade notes.
 */

export type NotificationLevel = 'info' | 'success' | 'warning' | 'error'

export interface ModuleSettings {
  get<T = unknown>(key: string, defaultValue?: T): Promise<T>
  set(key: string, value: unknown): Promise<void>
  delete(key: string): Promise<void>
  all(): Promise<Record<string, unknown>>
}

const notificationsSDK = {
  push: (_n: { title: string; message: string; level?: NotificationLevel }): void => {
    throw new Error('[TechForge SDK] notifications.push available in Phase 4.')
  },
}

const settingsSDK: ModuleSettings = {
  get: async <T>(_key: string, _defaultValue?: T): Promise<T> => {
    throw new Error('[TechForge SDK] settings.get available in Phase 4.')
  },
  set: async (): Promise<void> => {
    throw new Error('[TechForge SDK] settings.set available in Phase 4.')
  },
  delete: async (): Promise<void> => {
    throw new Error('[TechForge SDK] settings.delete available in Phase 4.')
  },
  all: async (): Promise<Record<string, unknown>> => {
    throw new Error('[TechForge SDK] settings.all available in Phase 4.')
  },
}

const navigationSDK = {
  registerNavItem: (_item: { id: string; label: string; path: string; icon?: string }): void => {
    throw new Error('[TechForge SDK] navigation.registerNavItem available in Phase 4.')
  },
}

export const sdk = {
  notifications: notificationsSDK,
  settings:      settingsSDK,
  navigation:    navigationSDK,
}

export default sdk
