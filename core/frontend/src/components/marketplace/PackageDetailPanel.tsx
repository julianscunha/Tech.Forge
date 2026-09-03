import { X, ExternalLink, ShieldCheck, Hash } from 'lucide-react'
import { cn } from '@/lib/utils'
import { CompatibilityBadge } from './CompatibilityBadge'
import { TrustBadge } from './TrustBadge'
import type { PackageInfo } from '@/types'

interface Props {
  pkg: PackageInfo
  onClose: () => void
}

export function PackageDetailPanel({ pkg, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-stretch justify-end" onClick={onClose}>
      <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px]" />

      <div
        className={cn(
          'relative z-10 w-full max-w-md flex flex-col',
          'bg-[hsl(var(--bg-elevated))] border-l border-[hsl(var(--border))]',
          'animate-slide-in-right overflow-hidden',
        )}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[hsl(var(--border-subtle))]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[hsl(var(--accent-muted))] flex items-center justify-center">
              <span className="text-xs font-bold text-[hsl(var(--accent))]">
                {pkg.category.slice(0, 2).toUpperCase()}
              </span>
            </div>
            <div>
              <p className="text-sm font-semibold text-[hsl(var(--text))]">{pkg.name}</p>
              <p className="text-xs font-mono text-[hsl(var(--text-muted))]">{pkg.module_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded flex items-center justify-center text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] hover:bg-[hsl(var(--bg-subtle))] transition-colors"
          >
            <X size={14} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">

          {/* Status badges */}
          <div className="flex items-center gap-2 flex-wrap">
            <CompatibilityBadge level={pkg.compatibility} />
            <TrustBadge level={pkg.trust_level} />
            {pkg.is_installed && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-[hsl(var(--success)/0.12)] text-[hsl(var(--success))]">
                Instalado
              </span>
            )}
            {pkg.has_update && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-[hsl(var(--warning)/0.12)] text-[hsl(var(--warning))]">
                Atualização disponível
              </span>
            )}
          </div>

          {/* Identity */}
          <Section title="Identificação">
            <Field label="Nome"      value={pkg.name} />
            <Field label="Vendor"    value={pkg.vendor} />
            <Field label="Autor"     value={pkg.author} />
            <Field label="Categoria" value={pkg.category} />
            <Field label="Versão disponível"  value={pkg.version} mono />
            {pkg.installed_version && (
              <Field label="Versão instalada" value={pkg.installed_version} mono />
            )}
          </Section>

          {/* Compatibility */}
          <Section title="Compatibilidade">
            <Field label="Mín. plataforma" value={pkg.platform_min_version} mono />
            <Field label="Máx. plataforma" value={pkg.platform_max_version} mono />
          </Section>

          {/* Description */}
          <Section title="Descrição">
            <p className="text-xs text-[hsl(var(--text-muted))] leading-relaxed">
              {pkg.description}
            </p>
          </Section>

          {/* Security */}
          <Section title="Segurança">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[hsl(var(--text-muted))] flex items-center gap-1">
                  <ShieldCheck size={11} /> Publisher
                </span>
                <span className="text-xs text-[hsl(var(--text-subtle))]">
                  {pkg.publisher ?? '—'}
                </span>
              </div>
              <div className="flex items-start justify-between gap-4">
                <span className="text-xs text-[hsl(var(--text-muted))] flex items-center gap-1 flex-shrink-0">
                  <Hash size={11} /> Checksum
                </span>
                <span className="text-[10px] font-mono text-[hsl(var(--text-subtle))] truncate text-right">
                  {pkg.checksum ? pkg.checksum.slice(0, 20) + '…' : '—'}
                </span>
              </div>
            </div>
            <p className="text-[10px] text-[hsl(var(--text-subtle))] mt-2 italic">
              Assinatura digital disponível na Fase 5.
            </p>
          </Section>

          {/* Links */}
          {(pkg.homepage || pkg.documentation) && (
            <Section title="Links">
              {pkg.homepage && (
                <a href={pkg.homepage} target="_blank" rel="noreferrer"
                  className="flex items-center gap-1.5 text-xs text-[hsl(var(--accent))] hover:underline">
                  <ExternalLink size={11} /> Homepage
                </a>
              )}
              {pkg.documentation && (
                <a href={pkg.documentation} target="_blank" rel="noreferrer"
                  className="flex items-center gap-1.5 text-xs text-[hsl(var(--accent))] hover:underline">
                  <ExternalLink size={11} /> Documentation
                </a>
              )}
            </Section>
          )}
        </div>
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-[10px] font-medium uppercase tracking-widest text-[hsl(var(--text-subtle))] mb-2">
        {title}
      </p>
      <div className="space-y-1.5">{children}</div>
    </div>
  )
}

function Field({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-xs text-[hsl(var(--text-muted))] flex-shrink-0">{label}</span>
      <span className={cn('text-xs truncate text-right',
        mono ? 'font-mono text-[hsl(var(--accent))]' : 'text-[hsl(var(--text))]'
      )}>{value}</span>
    </div>
  )
}
