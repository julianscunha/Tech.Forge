import { CheckCircle2, XCircle, AlertTriangle, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  success: boolean
  message: string
  status?: string
  onDismiss: () => void
}

export function OperationFeedback({ success, message, status, onDismiss }: Props) {
  const isIncompat = status === 'incompatible'
  const isWarning  = !success && isIncompat

  return (
    <div className={cn(
      'fixed bottom-6 right-6 z-50 flex items-start gap-3 px-4 py-3 rounded-lg shadow-xl',
      'border animate-fade-in max-w-sm',
      success
        ? 'bg-[hsl(var(--bg-elevated))] border-[hsl(var(--success)/0.3)] border-l-4 border-l-[hsl(var(--success))]'
        : isWarning
        ? 'bg-[hsl(var(--bg-elevated))] border-[hsl(var(--warning)/0.3)] border-l-4 border-l-[hsl(var(--warning))]'
        : 'bg-[hsl(var(--bg-elevated))] border-[hsl(var(--danger)/0.3)] border-l-4 border-l-[hsl(var(--danger))]',
    )}>
      {success
        ? <CheckCircle2 size={15} className="text-[hsl(var(--success))] flex-shrink-0 mt-0.5" />
        : isWarning
        ? <AlertTriangle size={15} className="text-[hsl(var(--warning))] flex-shrink-0 mt-0.5" />
        : <XCircle      size={15} className="text-[hsl(var(--danger))] flex-shrink-0 mt-0.5" />}

      <p className="text-xs text-[hsl(var(--text))] flex-1 leading-relaxed">{message}</p>

      <button
        onClick={onDismiss}
        className="text-[hsl(var(--text-subtle))] hover:text-[hsl(var(--text))] flex-shrink-0"
      >
        <X size={13} />
      </button>
    </div>
  )
}
