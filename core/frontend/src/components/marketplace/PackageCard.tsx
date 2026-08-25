import { ArrowUpCircle, CheckCircle2, ChevronRight, Download, Trash2, RefreshCw, Power, Play } from 'lucide-react'
import { cn } from '@/lib/utils'
import { CompatibilityBadge } from './CompatibilityBadge'
import { TrustBadge } from './TrustBadge'
import type { PackageInfo } from '@/types'

type Tab = 'installed' | 'available' | 'updates'

interface Props {
  pkg: PackageInfo
  tab: Tab
  loading?: boolean
  onInstall?: (pkg: PackageInfo) => void
  onRemove?:  (pkg: PackageInfo) => void
  onUpdate?:  (pkg: PackageInfo) => void
  onActivate?:   (pkg: PackageInfo) => void
  onDeactivate?: (pkg: PackageInfo) => void
  onClick?:   (pkg: PackageInfo) => void
}

export function PackageCard({ pkg, tab, loading, onInstall, onRemove, onUpdate, onActivate, onDeactivate, onClick }: Props) {
  const isIncompat = pkg.compatibility === 'incompatible'

  return (
    <div
      className={cn(
        'rounded-lg border border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-elevated))]',
        'flex flex-col gap-0 overflow-hidden',
        'hover:border-[hsl(var(--border))] transition-colors',
        isIncompat && 'opacity-70',
      )}
    >
      {/* Body — clickable */}
      <button
        onClick={() => onClick?.(pkg)}
        className="text-left px-4 py-3.5 flex items-start gap-3 flex-1"
      >
        {/* Icon */}
        <div className={cn(
          'w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5',
          'bg-[hsl(var(--accent-muted))]',
        )}>
          <span className="text-[11px] font-bold text-[hsl(var(--accent))]">
            {pkg.category.slice(0, 2).toUpperCase()}
          </span>
        </div>

        <div className="min-w-0 flex-1">
          {/* Title row */}
          <div className="flex items-center gap-2 flex-wrap mb-0.5">
            <span className="text-sm font-medium text-[hsl(var(--text))] truncate">{pkg.name}</span>
            {tab === 'updates' && (
              <span className="text-[10px] font-mono text-[hsl(var(--warning))]">
                v{pkg.installed_version} → v{pkg.version}
              </span>
            )}
            {tab === 'installed' && (
              <span className="text-[10px] font-mono text-[hsl(var(--text-subtle))]">
                v{pkg.version}
              </span>
            )}
            {tab === 'available' && (
              <span className="text-[10px] font-mono text-[hsl(var(--text-subtle))]">
                v{pkg.version}
              </span>
            )}
          </div>

          {/* Meta */}
          <p className="text-[11px] text-[hsl(var(--text-subtle))] mb-1.5">
            {pkg.vendor} · {pkg.category}
          </p>

          {/* Description */}
          <p className="text-xs text-[hsl(var(--text-muted))] line-clamp-2 leading-relaxed">
            {pkg.description}
          </p>

          {/* Badges */}
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <CompatibilityBadge level={pkg.compatibility} />
            <TrustBadge level={pkg.trust_level} />
            {tab === 'installed' && (
              <span className="inline-flex items-center gap-1 text-[10px] text-[hsl(var(--success))]">
                <CheckCircle2 size={10} /> Installed
              </span>
            )}
          </div>
        </div>

        <ChevronRight size={13} className="text-[hsl(var(--text-subtle))] flex-shrink-0 mt-1" />
      </button>

      {/* Action footer */}
      <div className="px-4 py-2 border-t border-[hsl(var(--border-subtle))] flex items-center justify-end gap-2 bg-[hsl(var(--bg))]">
        {tab === 'available' && !pkg.is_installed && (
          <ActionBtn
            icon={Download}
            label="Instalar"
            disabled={isIncompat || loading}
            loading={loading}
            onClick={() => onInstall?.(pkg)}
            variant="primary"
          />
        )}
        {tab === 'available' && pkg.is_installed && (
          <span className="text-[10px] text-[hsl(var(--text-subtle))]">Já instalado</span>
        )}
        {tab === 'installed' && (
          <ActionBtn
            icon={Trash2}
            label="Remover"
            disabled={loading}
            loading={loading}
            onClick={() => onRemove?.(pkg)}
            variant="danger"
          />
        )}
        {tab === 'installed' && pkg.is_enabled !== false && (
          <ActionBtn
            icon={Power}
            label="Desativar"
            disabled={loading}
            loading={loading}
            onClick={() => onDeactivate?.(pkg)}
            variant="muted"
          />
        )}
        {tab === 'installed' && pkg.is_enabled === false && (
          <ActionBtn
            icon={Play}
            label="Ativar"
            disabled={loading}
            loading={loading}
            onClick={() => onActivate?.(pkg)}
            variant="primary"
          />
        )}
        {tab === 'updates' && (
          <ActionBtn
            icon={ArrowUpCircle}
            label={`Atualizar para v${pkg.version}`}
            disabled={isIncompat || loading}
            loading={loading}
            onClick={() => onUpdate?.(pkg)}
            variant="accent"
          />
        )}
      </div>
    </div>
  )
}

// ── Small reusable action button ──────────────────────────────────────────────
type Variant = 'primary' | 'danger' | 'accent' | 'muted'

const variantCls: Record<Variant, string> = {
  primary: 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))] hover:bg-[hsl(var(--accent)/0.2)]',
  danger:  'bg-[hsl(var(--danger)/0.1)] text-[hsl(var(--danger))] hover:bg-[hsl(var(--danger)/0.2)]',
  accent:  'bg-[hsl(var(--warning)/0.1)] text-[hsl(var(--warning))] hover:bg-[hsl(var(--warning)/0.2)]',
  muted:   'bg-[hsl(var(--bg-subtle))] text-[hsl(var(--text-muted))] hover:bg-[hsl(var(--bg-subtle))]/70',
}

function ActionBtn({
  icon: Icon, label, disabled, loading, onClick, variant,
}: {
  icon: typeof Download
  label: string
  disabled?: boolean
  loading?: boolean
  onClick?: () => void
  variant: Variant
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-medium',
        'transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
        variantCls[variant],
      )}
    >
      {loading
        ? <RefreshCw size={11} className="animate-spin" />
        : <Icon size={11} />}
      {label}
    </button>
  )
}
