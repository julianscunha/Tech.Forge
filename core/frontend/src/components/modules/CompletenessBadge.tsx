import { CheckCircle2, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  score: number
  isComplete: boolean
  className?: string
}

export function CompletenessBadge({ score, isComplete, className }: Props) {
  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium',
      isComplete
        ? 'bg-[hsl(var(--success)/0.12)] text-[hsl(var(--success))]'
        : 'bg-[hsl(var(--warning)/0.12)] text-[hsl(var(--warning))]',
      className,
    )}>
      {isComplete
        ? <CheckCircle2 size={10} />
        : <AlertTriangle size={10} />}
      §16 {score.toFixed(0)}%
    </span>
  )
}
