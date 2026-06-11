import { ShieldCheck, Shield, ShieldAlert, ShieldOff } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { TrustLevel } from '@/types'

const CONFIG: Record<TrustLevel, {
  label: string
  icon: typeof ShieldCheck
  classes: string
}> = {
  verified:  { label: 'Verified',  icon: ShieldCheck, classes: 'text-[hsl(var(--success))]' },
  community: { label: 'Community', icon: Shield,      classes: 'text-[hsl(var(--accent))]'  },
  unsigned:  { label: 'Unsigned',  icon: ShieldAlert, classes: 'text-[hsl(var(--warning))]' },
  untrusted: { label: 'Untrusted', icon: ShieldOff,   classes: 'text-[hsl(var(--danger))]'  },
}

interface Props { level: TrustLevel; className?: string }

export function TrustBadge({ level, className }: Props) {
  const cfg = CONFIG[level] ?? CONFIG.unsigned
  const Icon = cfg.icon
  return (
    <span className={cn('inline-flex items-center gap-1 text-[10px] font-medium', cfg.classes, className)}>
      <Icon size={10} />
      {cfg.label}
    </span>
  )
}
