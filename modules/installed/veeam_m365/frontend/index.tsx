/**
 * veeam_m365 — Frontend Entry Point
 * ====================================
 * Module : veeam_m365
 * Name   : Veeam M365 Sizing
 * Icon   : shield-check
 * Color  : blue
 * Order  : 10
 */
import type { ModulePageConfig } from '../../../sdk/frontend/src/contracts/index'

export const moduleConfig: ModulePageConfig = {
  moduleId:    "veeam_m365",
  title:       "Veeam M365 Sizing",
  icon:        "shield-check",
  category:    "Backup",
  vendor:      "Veeam",
  route:       "/modules/veeam_m365",
  description: "Sizing para Microsoft 365.",
}

export default function VeeamM365Page() {
  return (
    <div className="p-8 space-y-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-[hsl(var(--accent-muted))] flex items-center justify-center">
          <span className="text-sm font-bold text-[hsl(var(--accent))]">VM</span>
        </div>
        <div>
          <h2 className="text-base font-semibold text-[hsl(var(--text))]">Veeam M365 Sizing</h2>
          <p className="text-xs text-[hsl(var(--text-muted))]">Veeam · v1.0.0 · Backup</p>
        </div>
      </div>
      <div className="rounded-lg border border-[hsl(var(--border-subtle))] p-4 bg-[hsl(var(--bg-elevated))]">
        <p className="text-xs text-[hsl(var(--text-muted))]">
          Sizing para Microsoft 365. Implementação pendente.
        </p>
      </div>
    </div>
  )
}

export function onMount(): void {}
export function onUnmount(): void {}
