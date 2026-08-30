import { useState } from 'react'
import { AlertTriangle, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
  checkboxLabel?: string
  checkboxDefault?: boolean
  onConfirm: (checkboxValue: boolean) => void
  onCancel: () => void
}

export function ConfirmDialog({
  title,
  message,
  confirmLabel = 'Confirmar',
  cancelLabel = 'Cancelar',
  danger = false,
  checkboxLabel,
  checkboxDefault = false,
  onConfirm,
  onCancel,
}: Props) {
  const [checked, setChecked] = useState(checkboxDefault)

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
      <div className={cn(
        'w-full max-w-md rounded-lg border border-[hsl(var(--border-subtle))]',
        'bg-[hsl(var(--bg-elevated))] shadow-lg flex flex-col',
      )}>
        {/* Header */}
        <div className="px-6 py-4 border-b border-[hsl(var(--border-subtle))] flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-base font-semibold text-[hsl(var(--text))]">
            {danger && <AlertTriangle size={16} className="text-[hsl(var(--danger))]" />}
            {title}
          </h2>
          <button
            onClick={onCancel}
            aria-label="Fechar"
            className="p-1 rounded hover:bg-[hsl(var(--bg-subtle))] text-[hsl(var(--text-muted))]"
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4">
          <p className="text-sm text-[hsl(var(--text-muted))] whitespace-pre-line">{message}</p>

          {checkboxLabel && (
            <label className="flex items-start gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={checked}
                onChange={e => setChecked(e.target.checked)}
                className="mt-0.5 rounded"
              />
              <span className="text-[hsl(var(--text))]">{checkboxLabel}</span>
            </label>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[hsl(var(--border-subtle))] flex items-center justify-end gap-2">
          <button
            onClick={onCancel}
            className={cn(
              'px-3 py-1.5 rounded text-xs font-medium',
              'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border))]',
              'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] hover:bg-[hsl(var(--bg-subtle))]',
              'transition-colors',
            )}
          >
            {cancelLabel}
          </button>
          <button
            onClick={() => onConfirm(checked)}
            className={cn(
              'px-3 py-1.5 rounded text-xs font-medium transition-colors',
              danger
                ? 'bg-[hsl(var(--danger)/0.1)] text-[hsl(var(--danger))] hover:bg-[hsl(var(--danger)/0.2)]'
                : 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))] hover:bg-[hsl(var(--accent)/0.2)]',
            )}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
