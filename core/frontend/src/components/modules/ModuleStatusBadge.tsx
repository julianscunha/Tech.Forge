import { cn } from '@/lib/utils'
import type { ModuleStatus } from '@/types'

const CONFIG: Record<ModuleStatus, { label: string; classes: string; dot: string }> = {
  INSTALLED:    { label: 'Installed',    classes: 'bg-[hsl(var(--success)/0.12)] text-[hsl(var(--success))]',    dot: 'bg-[hsl(var(--success))]' },
  DISABLED:     { label: 'Disabled',    classes: 'bg-[hsl(var(--text-subtle)/0.12)] text-[hsl(var(--text-muted))]', dot: 'bg-[hsl(var(--text-subtle))]' },
  INVALID:      { label: 'Invalid',     classes: 'bg-[hsl(var(--danger)/0.12)] text-[hsl(var(--danger))]',      dot: 'bg-[hsl(var(--danger))]' },
  INCOMPATIBLE: { label: 'Incompatible', classes: 'bg-[hsl(var(--warning)/0.12)] text-[hsl(var(--warning))]',   dot: 'bg-[hsl(var(--warning))]' },
  BLOCKED:      { label: 'Blocked',     classes: 'bg-[hsl(var(--danger)/0.12)] text-[hsl(var(--danger))]',      dot: 'bg-[hsl(var(--danger))]' },
}

interface Props {
  status: ModuleStatus
  className?: string
}

export function ModuleStatusBadge({ status, className }: Props) {
  const cfg = CONFIG[status]
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium',
        cfg.classes,
        className
      )}
    >
      <span className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0', cfg.dot,
        status === 'INSTALLED' && 'animate-pulse'
      )} />
      {cfg.label}
    </span>
  )
}
