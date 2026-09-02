import { AlertCircle, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ModuleStatusBadge } from './ModuleStatusBadge'
import { ModuleTypeBadge } from './ModuleTypeBadge'
import { CompletenessBadge } from './CompletenessBadge'
import { TrustBadge } from '@/components/marketplace/TrustBadge'
import type { ModuleEntry, CompletenessReport, ModuleTrust } from '@/types'

interface Props {
  module: ModuleEntry
  developerMode: boolean
  completeness?: CompletenessReport
  trust?: ModuleTrust
  onClick: (module: ModuleEntry) => void
}

export function ModuleCard({ module, developerMode, completeness, trust, onClick }: Props) {
  const hasIssues = module.errors.length > 0

  return (
    <button
      onClick={() => onClick(module)}
      className={cn(
        'w-full text-left rounded-lg p-4',
        'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border-subtle))]',
        'hover:border-[hsl(var(--border))] hover:bg-[hsl(var(--bg-subtle))]',
        'transition-all group'
      )}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2.5 min-w-0">
          {/* Category dot */}
          <div className="w-7 h-7 rounded-md bg-[hsl(var(--accent-muted))] flex items-center justify-center flex-shrink-0">
            <span className="text-[10px] font-bold text-[hsl(var(--accent))]">
              {module.category.slice(0, 2).toUpperCase()}
            </span>
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-[hsl(var(--text))] truncate leading-tight">
              {module.name}
            </p>
            <p className="text-xs text-[hsl(var(--text-subtle))] font-mono mt-0.5">
              {module.vendor} · v{module.version}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {trust && <TrustBadge level={trust.trust_level} />}
          <ModuleStatusBadge status={module.status} />
          <ChevronRight
            size={13}
            className="text-[hsl(var(--text-subtle))] group-hover:text-[hsl(var(--text-muted))] transition-colors"
          />
        </div>
      </div>

      {/* Documentation completeness */}
      {completeness && (
        <div className="mb-2">
          <CompletenessBadge score={completeness.score} isComplete={completeness.is_complete} />
        </div>
      )}

      {/* Description */}
      <p className="text-xs text-[hsl(var(--text-muted))] line-clamp-2 leading-relaxed">
        {module.description}
      </p>

      {/* Category tag */}
      <div className="flex items-center gap-2 mt-2.5">
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium
          bg-[hsl(var(--bg-subtle))] text-[hsl(var(--text-muted))]">
          {module.category}
        </span>

        <ModuleTypeBadge moduleType={module.module_type} />

        {hasIssues && (
          <span className="flex items-center gap-1 text-[10px] text-[hsl(var(--danger))]">
            <AlertCircle size={10} />
            {module.errors.length} {module.errors.length === 1 ? 'error' : 'errors'}
          </span>
        )}

        {/* Developer Mode: show module_id */}
        {developerMode && (
          <span className="ml-auto text-[10px] font-mono text-[hsl(var(--text-subtle))]">
            {module.module_id}
          </span>
        )}
      </div>
    </button>
  )
}
