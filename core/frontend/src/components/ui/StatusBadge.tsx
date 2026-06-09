import { cn } from '@/lib/utils'

type Status = 'online' | 'connected' | 'degraded' | 'offline' | 'error'

const STATUS_CONFIG: Record<Status, { label: string; dotClass: string; textClass: string }> = {
  online:    { label: 'Online',     dotClass: 'bg-[hsl(var(--success))]', textClass: 'text-[hsl(var(--success))]' },
  connected: { label: 'Conectado',  dotClass: 'bg-[hsl(var(--success))]', textClass: 'text-[hsl(var(--success))]' },
  degraded:  { label: 'Degradado',  dotClass: 'bg-[hsl(var(--warning))]', textClass: 'text-[hsl(var(--warning))]' },
  offline:   { label: 'Offline',    dotClass: 'bg-[hsl(var(--danger))]',  textClass: 'text-[hsl(var(--danger))]' },
  error:     { label: 'Erro',       dotClass: 'bg-[hsl(var(--danger))]',  textClass: 'text-[hsl(var(--danger))]' },
}

interface StatusBadgeProps {
  status: Status
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status]
  return (
    <span className={cn('flex items-center gap-1.5', className)}>
      <span
        className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0', config.dotClass, 'animate-pulse')}
      />
      <span className={cn('text-xs font-medium', config.textClass)}>{config.label}</span>
    </span>
  )
}
