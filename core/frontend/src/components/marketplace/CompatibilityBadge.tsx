import { cn } from '@/lib/utils'
import type { CompatibilityLevel } from '@/types'

const CONFIG: Record<CompatibilityLevel, { label: string; classes: string; dot: string }> = {
  compatible:   { label: 'Compatível',   classes: 'bg-[hsl(var(--success)/0.12)] text-[hsl(var(--success))]',  dot: 'bg-[hsl(var(--success))]' },
  warning:      { label: 'Atenção',      classes: 'bg-[hsl(var(--warning)/0.12)] text-[hsl(var(--warning))]', dot: 'bg-[hsl(var(--warning))]' },
  incompatible: { label: 'Incompatível', classes: 'bg-[hsl(var(--danger)/0.12)] text-[hsl(var(--danger))]',   dot: 'bg-[hsl(var(--danger))]'  },
}

interface Props {
  level: CompatibilityLevel
  className?: string
}

export function CompatibilityBadge({ level, className }: Props) {
  const cfg = CONFIG[level] ?? CONFIG.incompatible
  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium',
      cfg.classes, className,
    )}>
      <span className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0', cfg.dot)} />
      {cfg.label}
    </span>
  )
}
