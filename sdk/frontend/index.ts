/**
 * TechForge SDK — Frontend (TypeScript)
 * ======================================
 * Stub for the official frontend SDK used by module UIs.
 *
 * In Phase 2 (Module Loader), these will be fully implemented.
 * Modules import from this package instead of duplicating UI primitives.
 *
 * Usage (module frontend):
 *   import { sdk } from '@techforge/sdk'
 *   sdk.notifications.push({ title: 'Done', message: 'Task complete' })
 */

// ── UI Components — re-exported from Core ─────────────────────────────────────
// Phase 2+: modules import these instead of duplicating shadcn components
export * from '../core/frontend/src/components/ui/StatCard'
export * from '../core/frontend/src/components/ui/StatusBadge'
export * from '../core/frontend/src/components/ui/ComingSoon'

// ── SDK services ──────────────────────────────────────────────────────────────

interface Notification {
  title: string
  message: string
  level?: 'info' | 'success' | 'warning' | 'error'
}

const notificationsSDK = {
  /** Phase 2: will dispatch to the Core notification store */
  push: (_notification: Notification): void => {
    throw new Error('SDK: notifications available in Phase 2')
  },
}

const settingsSDK = {
  /** Phase 2: reads per-module settings from the backend */
  get: (_key: string): Promise<unknown> => {
    throw new Error('SDK: settings available in Phase 2')
  },
}

export const sdk = {
  notifications: notificationsSDK,
  settings: settingsSDK,
}

export default sdk
