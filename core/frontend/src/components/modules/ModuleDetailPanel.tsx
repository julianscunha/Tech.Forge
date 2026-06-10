import { X, AlertCircle, AlertTriangle, Terminal } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ModuleStatusBadge } from './ModuleStatusBadge'
import type { ModuleEntry } from '@/types'

interface Props {
  module: ModuleEntry
  developerMode: boolean
  onClose: () => void
}

export function ModuleDetailPanel({ module, developerMode, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-stretch justify-end" onClick={onClose}>
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px]" />

      {/* Panel */}
      <div
        className={cn(
          'relative z-10 w-full max-w-md flex flex-col',
          'bg-[hsl(var(--bg-elevated))] border-l border-[hsl(var(--border))]',
          'animate-slide-in-right overflow-hidden'
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Panel header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[hsl(var(--border-subtle))]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-[hsl(var(--accent-muted))] flex items-center justify-center">
              <span className="text-xs font-bold text-[hsl(var(--accent))]">
                {module.category.slice(0, 2).toUpperCase()}
              </span>
            </div>
            <div>
              <p className="text-sm font-semibold text-[hsl(var(--text))]">{module.name}</p>
              <p className="text-xs font-mono text-[hsl(var(--text-muted))]">{module.module_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className={cn(
              'w-7 h-7 rounded flex items-center justify-center',
              'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
              'hover:bg-[hsl(var(--bg-subtle))] transition-colors'
            )}
          >
            <X size={14} />
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
          {/* Status */}
          <div>
            <Label>Status</Label>
            <ModuleStatusBadge status={module.status} />
          </div>

          {/* Identity */}
          <Section title="Identificação">
            <Field label="Nome"    value={module.name} />
            <Field label="Vendor"  value={module.vendor} />
            <Field label="Autor"   value={module.author} />
            <Field label="Versão"  value={module.version} mono />
            <Field label="Categoria" value={module.category} />
          </Section>

          {/* Compatibility */}
          <Section title="Compatibilidade">
            <Field label="Versão mínima" value={module.platform_min_version} mono />
            <Field label="Versão máxima" value={module.platform_max_version} mono />
          </Section>

          {/* Description */}
          <Section title="Descrição">
            <p className="text-xs text-[hsl(var(--text-muted))] leading-relaxed">
              {module.description}
            </p>
          </Section>

          {/* Errors */}
          {module.errors.length > 0 && (
            <Section title="Erros">
              {module.errors.map((err, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-[hsl(var(--danger))]">
                  <AlertCircle size={12} className="flex-shrink-0 mt-0.5" />
                  <span>{err}</span>
                </div>
              ))}
            </Section>
          )}

          {/* Warnings */}
          {module.warnings.length > 0 && (
            <Section title="Avisos">
              {module.warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-[hsl(var(--warning))]">
                  <AlertTriangle size={12} className="flex-shrink-0 mt-0.5" />
                  <span>{w}</span>
                </div>
              ))}
            </Section>
          )}

          {/* Developer Mode extras */}
          {developerMode && (
            <>
              <Section title="Entry Points (Developer Mode)">
                <Field label="Backend"  value={module.entry_backend ?? '—'} mono />
                <Field label="Frontend" value={module.entry_frontend ?? '—'} mono />
              </Section>

              {module.manifest_raw && (
                <Section title="Manifesto Raw (Developer Mode)">
                  <div className="flex items-center gap-1.5 mb-2">
                    <Terminal size={11} className="text-[hsl(var(--accent))]" />
                    <span className="text-[10px] font-medium text-[hsl(var(--accent))]">manifest.yaml</span>
                  </div>
                  <pre className={cn(
                    'text-[10px] font-mono leading-relaxed',
                    'bg-[hsl(var(--bg))] border border-[hsl(var(--border-subtle))]',
                    'rounded p-3 overflow-x-auto whitespace-pre-wrap',
                    'text-[hsl(var(--text-muted))]'
                  )}>
                    {JSON.stringify(module.manifest_raw, null, 2)}
                  </pre>
                </Section>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Small helpers ─────────────────────────────────────────────────────────────

function Label({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[10px] font-medium uppercase tracking-widest text-[hsl(var(--text-subtle))] mb-1.5">
      {children}
    </p>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <Label>{title}</Label>
      <div className="space-y-1.5">{children}</div>
    </div>
  )
}

function Field({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-xs text-[hsl(var(--text-muted))] flex-shrink-0">{label}</span>
      <span className={cn(
        'text-xs text-[hsl(var(--text))] truncate text-right',
        mono && 'font-mono text-[hsl(var(--accent))]'
      )}>
        {value}
      </span>
    </div>
  )
}
