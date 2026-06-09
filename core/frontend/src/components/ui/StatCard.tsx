import { cn } from '@/lib/utils'
import type { LucideIcon } from 'lucide-react'

interface StatCardProps {
  label: string
  value: string | number
  icon?: LucideIcon
  description?: string
  className?: string
}

export function StatCard({ label, value, icon: Icon, description, className }: StatCardProps) {
  return (
    <div
      className={cn(
        'rounded-lg p-4',
        'bg-[hsl(var(--bg-elevated))]',
        'border border-[hsl(var(--border-subtle))]',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs text-[hsl(var(--text-muted))] font-medium uppercase tracking-wide">
            {label}
          </p>
          <p className="text-2xl font-semibold text-[hsl(var(--text))] font-mono tabular-nums">
            {value}
          </p>
          {description && (
            <p className="text-xs text-[hsl(var(--text-subtle))]">{description}</p>
          )}
        </div>

        {Icon && (
          <div className="w-8 h-8 rounded-md bg-[hsl(var(--accent-muted))] flex items-center justify-center flex-shrink-0">
            <Icon size={15} className="text-[hsl(var(--accent))]" />
          </div>
        )}
      </div>
    </div>
  )
}
