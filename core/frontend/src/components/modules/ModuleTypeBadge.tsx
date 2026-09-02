import { AppWindow, Server } from 'lucide-react'
import { cn } from '@/lib/utils'

const CONFIG: Record<string, { label: string; classes: string; Icon: typeof Server }> = {
  service: {
    label: 'Service',
    classes: 'bg-[hsl(var(--info)/0.12)] text-[hsl(var(--info))]',
    Icon: Server,
  },
  application: {
    label: 'Application',
    classes: 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))]',
    Icon: AppWindow,
  },
}

interface Props {
  moduleType: string
  className?: string
}

// Diferenciação visual entre Service Module (sem UI, consumido via SDK por
// outros módulos) e Application Module (tem UI própria) — module_type existia
// só no backend até aqui, nunca chegava ao frontend.
export function ModuleTypeBadge({ moduleType, className }: Props) {
  const cfg = CONFIG[moduleType] ?? CONFIG.application
  const { Icon } = cfg
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium',
        cfg.classes,
        className
      )}
    >
      <Icon size={10} />
      {cfg.label}
    </span>
  )
}
