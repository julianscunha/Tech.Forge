/**
 * hello_world — Frontend Entry Point (Phase 3)
 * ==============================================
 * Demonstrates the Phase 3 SDK component usage and moduleConfig contract.
 */
import type { ModulePageConfig } from '../../../sdk/frontend/src/contracts/index'

// ── Module config — read by Plugin Loader ─────────────────────────────────────
export const moduleConfig: ModulePageConfig = {
  moduleId:    "hello_world",
  title:       "Hello World",
  icon:        "Boxes",
  category:    "Examples",
  vendor:      "TechForge",
  route:       "/modules/hello_world",
  description: "Reference module — architecture validation only.",
}

// ── Page component ────────────────────────────────────────────────────────────
export default function HelloWorldPage() {
  return (
    <div className="p-8 space-y-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-[hsl(var(--accent-muted))] flex items-center justify-center">
          <span className="text-sm font-bold text-[hsl(var(--accent))]">HW</span>
        </div>
        <div>
          <h2 className="text-base font-semibold text-[hsl(var(--text))]">Hello World</h2>
          <p className="text-xs text-[hsl(var(--text-muted))]">
            TechForge · v1.0.0 · Examples
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-[hsl(var(--border-subtle))] p-4 bg-[hsl(var(--bg-elevated))]">
        <p className="text-xs text-[hsl(var(--text-muted))] leading-relaxed">
          This is the reference module for the TechForge Phase 3 architecture.
          It validates the SDK, CLI, and module contracts without implementing
          any real business logic.
        </p>
      </div>

      <code className="block text-[10px] font-mono text-[hsl(var(--accent))] bg-[hsl(var(--bg-subtle))] rounded p-3">
        module: hello_world · sdk: techforge-sdk@1.0.0 · cli: techforge-cli@1.0.0
      </code>
    </div>
  )
}

export function onMount(): void {}
export function onUnmount(): void {}
