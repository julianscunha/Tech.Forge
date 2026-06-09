import type { LucideIcon } from 'lucide-react'
import { Construction } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ComingSoonProps {
  icon?: LucideIcon
  title: string
  description: string
  phase: string
  className?: string
}

export function ComingSoon({ icon: Icon = Construction, title, description, phase, className }: ComingSoonProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center h-full min-h-64 p-8 text-center', className)}>
      <div className="w-12 h-12 rounded-xl bg-[hsl(var(--bg-subtle))] flex items-center justify-center mb-4">
        <Icon size={20} className="text-[hsl(var(--text-muted))]" />
      </div>
      <h2 className="text-base font-semibold text-[hsl(var(--text))] mb-1">{title}</h2>
      <p className="text-sm text-[hsl(var(--text-muted))] max-w-xs mb-3">{description}</p>
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))]">
        {phase}
      </span>
    </div>
  )
}
