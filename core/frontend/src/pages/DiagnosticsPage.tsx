import { useCallback, useEffect, useState } from 'react'
import {
  Activity, RefreshCw, AlertCircle, Download, CheckCircle2, XCircle,
} from 'lucide-react'
import { diagnosticsApi } from '@/lib/api'
import type { DiagnosticsHealth, DiagnosticError, ExecutionEntry } from '@/types'
import { cn } from '@/lib/utils'

type LoadState = 'idle' | 'loading' | 'success' | 'error'

export function DiagnosticsPage() {
  const [health, setHealth] = useState<DiagnosticsHealth | null>(null)
  const [errors, setErrors] = useState<DiagnosticError[]>([])
  const [executions, setExecutions] = useState<ExecutionEntry[]>([])
  const [loadState, setLoadState] = useState<LoadState>('idle')
  const [apiError, setApiError] = useState<string | null>(null)
  const [exporting, setExporting] = useState<'json' | 'txt' | 'zip' | null>(null)

  const fetchAll = useCallback(async () => {
    setLoadState('loading')
    setApiError(null)
    try {
      const [h, errs, execs] = await Promise.all([
        diagnosticsApi.health(),
        diagnosticsApi.errors(50),
        diagnosticsApi.executions(50),
      ])
      setHealth(h)
      setErrors(errs)
      setExecutions(execs)
      setLoadState('success')
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'Erro desconhecido')
      setLoadState('error')
    }
  }, [])

  useEffect(() => { fetchAll() }, [fetchAll])

  const handleExport = async (format: 'json' | 'txt' | 'zip') => {
    setExporting(format)
    try {
      const blob = await diagnosticsApi.exportReport(format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = format === 'zip' ? 'techforge-support-bundle.zip' : `techforge-diagnostics.${format}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch {
      setApiError('Falha ao exportar diagnóstico.')
    } finally {
      setExporting(null)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 pt-4 pb-4 flex-shrink-0">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-lg font-semibold text-[hsl(var(--text))] tracking-tight flex items-center gap-2">
              <Activity size={17} className="text-[hsl(var(--accent))]" />
              Diagnostics
            </h1>
            <p className="text-sm text-[hsl(var(--text-muted))] mt-0.5">
              Health, erros e execuções recentes da plataforma
            </p>
          </div>

          <div className="flex items-center gap-2">
            <ExportButton format="json" exporting={exporting} onClick={() => handleExport('json')} />
            <ExportButton format="txt" exporting={exporting} onClick={() => handleExport('txt')} />
            <ExportButton format="zip" exporting={exporting} onClick={() => handleExport('zip')} label="Support Bundle" />
            <button
              onClick={fetchAll}
              disabled={loadState === 'loading'}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium',
                'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border))]',
                'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
                'hover:bg-[hsl(var(--bg-subtle))] transition-colors',
                'disabled:opacity-50 disabled:cursor-not-allowed',
              )}
            >
              <RefreshCw size={12} className={loadState === 'loading' ? 'animate-spin' : ''} />
              Atualizar
            </button>
          </div>
        </div>
      </div>

      {apiError && (
        <div className="mx-6 mb-4 flex items-center gap-2 px-4 py-2.5 rounded-lg
          border border-[hsl(var(--danger)/0.3)] bg-[hsl(var(--danger)/0.06)]
          text-sm text-[hsl(var(--danger))]">
          <AlertCircle size={14} className="flex-shrink-0" />
          <span>{apiError}</span>
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-6">
        {/* Health */}
        {health && (
          <section>
            <SectionTitle>Health</SectionTitle>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <HealthCard label="Banco de Dados" ok={health.storage.database && health.platform.database_status === 'connected'} />
              <HealthCard label="Storage gravável" ok={health.storage.writable} />
              <HealthCard label="Runtime" ok={health.runtime.state === 'ready'} okLabel={health.runtime.state} />
            </div>
          </section>
        )}

        {/* Errors */}
        <section>
          <SectionTitle>Erros recentes ({errors.length})</SectionTitle>
          {errors.length === 0 ? (
            <EmptyRow text="Nenhum erro registrado." />
          ) : (
            <div className="rounded-lg border border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-elevated))] overflow-hidden">
              {errors.map((e) => (
                <div
                  key={e.id}
                  className="flex items-start gap-3 px-4 py-2.5 border-b border-[hsl(var(--border-subtle))] last:border-0 text-xs"
                >
                  <span className="font-mono text-[hsl(var(--danger))] flex-shrink-0 w-32 truncate">
                    {e.code ?? e.source}
                  </span>
                  <span className="text-[hsl(var(--text))] flex-1 min-w-0 truncate">{e.message}</span>
                  <span className="text-[hsl(var(--text-subtle))] flex-shrink-0">{e.module_id ?? '—'}</span>
                  <span className="text-[hsl(var(--text-subtle))] flex-shrink-0 font-mono">
                    {e.created_at ? new Date(e.created_at).toLocaleString('pt-BR') : '—'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Executions */}
        <section>
          <SectionTitle>Execuções recentes ({executions.length})</SectionTitle>
          {executions.length === 0 ? (
            <EmptyRow text="Nenhuma execução registrada." />
          ) : (
            <div className="rounded-lg border border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-elevated))] overflow-hidden">
              {executions.map((ex) => (
                <div
                  key={ex.execution_id}
                  className="flex items-center gap-3 px-4 py-2.5 border-b border-[hsl(var(--border-subtle))] last:border-0 text-xs"
                >
                  {ex.status === 'SUCCESS' ? (
                    <CheckCircle2 size={12} className="text-[hsl(var(--success))] flex-shrink-0" />
                  ) : (
                    <XCircle size={12} className="text-[hsl(var(--danger))] flex-shrink-0" />
                  )}
                  <span className="text-[hsl(var(--text))] flex-1 min-w-0 truncate">{ex.module_id}</span>
                  <span className="text-[hsl(var(--text-subtle))] font-mono flex-shrink-0">
                    {ex.duration_seconds.toFixed(3)}s
                  </span>
                  <span className="text-[hsl(var(--text-subtle))] flex-shrink-0 font-mono">
                    {ex.created_at ? new Date(ex.created_at).toLocaleString('pt-BR') : '—'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-xs font-medium text-[hsl(var(--text-muted))] uppercase tracking-wide mb-2">
      {children}
    </h2>
  )
}

function EmptyRow({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-elevated))] px-4 py-6 text-center">
      <p className="text-xs text-[hsl(var(--text-subtle))]">{text}</p>
    </div>
  )
}

function HealthCard({ label, ok, okLabel }: { label: string; ok: boolean; okLabel?: string }) {
  return (
    <div className="rounded-lg px-4 py-3 border border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-elevated))]">
      <p className="text-xs text-[hsl(var(--text-muted))] mb-1.5 uppercase tracking-wide font-medium">{label}</p>
      <div className={cn('flex items-center gap-1.5 text-sm font-medium',
        ok ? 'text-[hsl(var(--success))]' : 'text-[hsl(var(--danger))]')}>
        {ok ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
        {okLabel ?? (ok ? 'OK' : 'Falha')}
      </div>
    </div>
  )
}

function ExportButton({ format, exporting, onClick, label }: {
  format: 'json' | 'txt' | 'zip'
  exporting: string | null
  onClick: () => void
  label?: string
}) {
  return (
    <button
      onClick={onClick}
      disabled={exporting !== null}
      title={label ?? `Exportar ${format.toUpperCase()}`}
      className={cn(
        'flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium',
        'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border))]',
        'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
        'hover:bg-[hsl(var(--bg-subtle))] transition-colors',
        'disabled:opacity-50 disabled:cursor-not-allowed',
      )}
    >
      {exporting === format ? <RefreshCw size={12} className="animate-spin" /> : <Download size={12} />}
      {label ?? format.toUpperCase()}
    </button>
  )
}
