import { ChevronRight, Download, RefreshCw, Star, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { TrustBadge } from '../marketplace/TrustBadge'
import { catalogApi } from '@/lib/api'
import { useState } from 'react'
import type { CatalogModule } from '@/types'

interface Props {
  module: CatalogModule
  conflictCount?: number
  onInstall?: (module: CatalogModule) => void
  onClick?: (module: CatalogModule) => void
  loading?: boolean
}

export function CatalogCard({
  module,
  conflictCount,
  onInstall,
  onClick,
  loading = false,
}: Props) {
  const [isFavorite, setIsFavorite] = useState(module.favorite)
  const [favoriteLoading, setFavoriteLoading] = useState(false)

  const isIncompat = module.compatibility === 'incompatible'
  const sourceLabel = module.source === 'local' ? 'Local' : module.source === 'official_catalog' ? 'Oficial' : 'Custom'

  const handleFavoriteClick = async (e: React.MouseEvent) => {
    e.stopPropagation()
    setFavoriteLoading(true)
    try {
      if (isFavorite) {
        await catalogApi.unfavorite(module.module_id)
        setIsFavorite(false)
      } else {
        await catalogApi.favorite(module.module_id)
        setIsFavorite(true)
      }
    } catch (e) {
      console.error('Erro ao favoritar:', e)
    } finally {
      setFavoriteLoading(false)
    }
  }

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
        onClick={() => onClick?.(module)}
        className="text-left px-4 py-3.5 flex items-start gap-3 flex-1"
      >
        {/* Icon */}
        <div className={cn(
          'w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5',
          'bg-[hsl(var(--accent-muted))]',
        )}>
          <span className="text-[11px] font-bold text-[hsl(var(--accent))]">
            {module.name.slice(0, 2).toUpperCase()}
          </span>
        </div>

        <div className="min-w-0 flex-1">
          {/* Title row */}
          <div className="flex items-center gap-2 flex-wrap mb-0.5">
            <span className="text-sm font-medium text-[hsl(var(--text))] truncate">{module.name}</span>
            <span className="text-[10px] font-mono text-[hsl(var(--text-subtle))]">
              v{module.version}
            </span>
          </div>

          {/* Meta */}
          <p className="text-[11px] text-[hsl(var(--text-subtle))] mb-1.5">
            {module.vendor} · {module.category}
          </p>

          {/* Description */}
          <p className="text-xs text-[hsl(var(--text-muted))] line-clamp-2 leading-relaxed">
            {module.description}
          </p>

          {/* Badges */}
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <TrustBadge level={module.trust_level} />
            <span className="inline-flex items-center gap-1 text-[10px] text-[hsl(var(--text-subtle))]">
              {sourceLabel}
            </span>
            {conflictCount && conflictCount > 1 && (
              <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-[hsl(var(--warning)/0.1)] text-[hsl(var(--warning))]">
                Disponível em {conflictCount}
              </span>
            )}
            {module.is_installed && (
              <span className="inline-flex items-center gap-1 text-[10px] text-[hsl(var(--success))]">
                <Check size={10} /> Instalado
              </span>
            )}
          </div>
        </div>

        <ChevronRight size={13} className="text-[hsl(var(--text-subtle))] flex-shrink-0 mt-1" />
      </button>

      {/* Action footer */}
      <div className="px-4 py-2 border-t border-[hsl(var(--border-subtle))] flex items-center justify-between bg-[hsl(var(--bg))]">
        <button
          onClick={handleFavoriteClick}
          disabled={favoriteLoading}
          className={cn(
            'inline-flex items-center justify-center w-6 h-6 rounded transition-colors',
            isFavorite
              ? 'text-[hsl(var(--warning))]'
              : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--warning))]',
            favoriteLoading && 'opacity-50 cursor-not-allowed',
          )}
        >
          <Star size={16} fill={isFavorite ? 'currentColor' : 'none'} />
        </button>

        <div className="flex items-center gap-2">
          {!module.is_installed && (
            <ActionBtn
              icon={Download}
              label={module.source === 'local' ? 'Instalar' : 'Instalar'}
              disabled={isIncompat || loading}
              loading={loading}
              onClick={() => onInstall?.(module)}
              variant="primary"
            />
          )}
          {module.is_installed && module.has_update && (
            <ActionBtn
              icon={RefreshCw}
              label="Atualizar"
              disabled={loading}
              loading={loading}
              onClick={() => onInstall?.(module)}
              variant="accent"
            />
          )}
          {module.is_installed && !module.has_update && (
            <span className="text-[10px] text-[hsl(var(--text-subtle))]">Instalado</span>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Action button ────────────────────────────────────────────────────────
type Variant = 'primary' | 'accent' | 'danger' | 'muted'

const variantCls: Record<Variant, string> = {
  primary: 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))] hover:bg-[hsl(var(--accent)/0.2)]',
  accent:  'bg-[hsl(var(--warning)/0.1)] text-[hsl(var(--warning))] hover:bg-[hsl(var(--warning)/0.2)]',
  danger:  'bg-[hsl(var(--danger)/0.1)] text-[hsl(var(--danger))] hover:bg-[hsl(var(--danger)/0.2)]',
  muted:   'bg-[hsl(var(--bg-subtle))] text-[hsl(var(--text-muted))] hover:bg-[hsl(var(--bg-subtle))]/70',
}

function ActionBtn({
  icon: Icon,
  label,
  disabled,
  loading,
  onClick,
  variant,
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
