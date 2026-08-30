import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Siren } from 'lucide-react'
import { diagnosticsApi } from '@/lib/api'
import type { DiagnosticError } from '@/types'

export function RecentCriticalEventsCard() {
  const navigate = useNavigate()
  const [errors, setErrors] = useState<DiagnosticError[] | null>(null)

  useEffect(() => {
    diagnosticsApi.errors(3).then(setErrors).catch(() => setErrors([]))
  }, [])

  return (
    <button
      onClick={() => navigate('/diagnostics')}
      className="text-left w-full h-[104px] rounded-lg p-4 bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border-subtle))] overflow-hidden"
    >
      <div className="flex items-center gap-1.5 mb-2">
        <Siren size={12} className="text-[hsl(var(--text-muted))]" />
        <p className="text-xs text-[hsl(var(--text-muted))] font-medium uppercase tracking-wide">
          Recent Critical Events
        </p>
      </div>
      {errors === null ? (
        <p className="text-xs text-[hsl(var(--text-subtle))]">Carregando…</p>
      ) : errors.length === 0 ? (
        <p className="text-xs text-[hsl(var(--text-subtle))]">Nenhum evento recente.</p>
      ) : (
        <ul className="space-y-1.5">
          {errors.map((e) => (
            <li key={e.id} className="text-xs text-[hsl(var(--text))] truncate">
              <span className="font-mono text-[hsl(var(--danger))]">{e.code ?? e.source}</span>
              {' — '}
              <span className="text-[hsl(var(--text-muted))]">{e.message}</span>
            </li>
          ))}
        </ul>
      )}
    </button>
  )
}
