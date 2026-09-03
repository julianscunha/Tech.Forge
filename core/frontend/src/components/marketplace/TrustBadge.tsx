import { ShieldCheck, Shield, ShieldAlert, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { TrustLevel } from '@/types'

const CONFIG: Record<TrustLevel, {
  label: string
  icon: typeof ShieldCheck
  classes: string
}> = {
  TRUSTED:    { label: 'Confiável',   icon: ShieldCheck, classes: 'text-[hsl(var(--success))]' },
  VERIFIED:   { label: 'Verificado',  icon: Shield,      classes: 'text-[hsl(var(--accent))]'  },
  UNVERIFIED: { label: 'Não verificado', icon: ShieldAlert, classes: 'text-[hsl(var(--warning))]' },
  MODIFIED:   { label: 'Modificado', icon: ShieldAlert, classes: 'text-[hsl(var(--warning))]' },
  INVALID:    { label: 'Inválido',   icon: XCircle,     classes: 'text-[hsl(var(--danger))]'  },
}

interface Props { level: TrustLevel; className?: string }

export function TrustBadge({ level, className }: Props) {
  const cfg = CONFIG[level] ?? CONFIG.UNVERIFIED
  const Icon = cfg.icon
  return (
    <span className={cn('inline-flex items-center gap-1 text-[10px] font-medium', cfg.classes, className)}>
      <Icon size={10} />
      {cfg.label}
    </span>
  )
}
