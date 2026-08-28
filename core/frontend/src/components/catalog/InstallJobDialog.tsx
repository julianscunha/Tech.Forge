import { useEffect, useState, useCallback } from 'react'
import { X, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react'
import { installJobApi } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { InstallJob, InstallJobPhase } from '@/types'

interface Props {
  moduleId: string
  moduleName: string
  onClose: () => void
  onSuccess: () => void
}

const PHASE_LABELS: Record<InstallJobPhase, string> = {
  ACQUIRING: 'Baixando módulo...',
  VALIDATING: 'Validando...',
  INSTALLING: 'Instalando...',
  DONE: 'Concluído',
  FAILED: 'Falhou',
}

export function InstallJobDialog({
  moduleId,
  moduleName,
  onClose,
  onSuccess,
}: Props) {
  const [jobId, setJobId] = useState<string | null>(null)
  const [job, setJob] = useState<InstallJob | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isRetrying, setIsRetrying] = useState(false)

  // Start installation
  useEffect(() => {
    const start = async () => {
      try {
        const res = await installJobApi.installRemote(moduleId)
        setJobId(res.job_id)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Erro ao iniciar instalação')
      }
    }
    start()
  }, [moduleId])

  // Poll job status
  useEffect(() => {
    if (!jobId) return

    let interval: NodeJS.Timeout | null = null
    const poll = async () => {
      try {
        const j = await installJobApi.getJob(jobId)
        setJob(j)
        if (j.phase === 'DONE' || j.phase === 'FAILED') {
          if (interval) clearInterval(interval)
        }
      } catch (e) {
        console.error('Erro ao buscar job:', e)
      }
    }

    poll()
    interval = setInterval(poll, 800)

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [jobId])

  const handleRetry = useCallback(async () => {
    setIsRetrying(true)
    setJob(null)
    setError(null)
    try {
      const res = await installJobApi.installRemote(moduleId)
      setJobId(res.job_id)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao reiniciar instalação')
    } finally {
      setIsRetrying(false)
    }
  }, [moduleId])

  const isDone = job?.phase === 'DONE'
  const isFailed = job?.phase === 'FAILED'
  const isLoading = !job || (job.phase !== 'DONE' && job.phase !== 'FAILED')

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
      <div className={cn(
        'w-full max-w-md rounded-lg border border-[hsl(var(--border-subtle))]',
        'bg-[hsl(var(--bg-elevated))] shadow-lg',
        'flex flex-col',
      )}>
        {/* Header */}
        <div className="px-6 py-4 border-b border-[hsl(var(--border-subtle))] flex items-center justify-between">
          <h2 className="text-base font-semibold text-[hsl(var(--text))]">
            Instalando "{moduleName}"
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-[hsl(var(--bg-subtle))] text-[hsl(var(--text-muted))]"
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-6 space-y-4">
          {error && (
            <div className="flex items-start gap-3 p-3 rounded-lg bg-[hsl(var(--danger)/0.1)] border border-[hsl(var(--danger)/0.2)]">
              <AlertCircle size={16} className="text-[hsl(var(--danger))] flex-shrink-0 mt-0.5" />
              <p className="text-sm text-[hsl(var(--danger))]">{error}</p>
            </div>
          )}

          {isDone && (
            <div className="flex items-center gap-3 p-3 rounded-lg bg-[hsl(var(--success)/0.1)] border border-[hsl(var(--success)/0.2)]">
              <CheckCircle2 size={16} className="text-[hsl(var(--success))] flex-shrink-0" />
              <p className="text-sm text-[hsl(var(--success))] font-medium">Instalado com sucesso!</p>
            </div>
          )}

          {isFailed && job?.error && (
            <div className="flex items-start gap-3 p-3 rounded-lg bg-[hsl(var(--danger)/0.1)] border border-[hsl(var(--danger)/0.2)]">
              <AlertCircle size={16} className="text-[hsl(var(--danger))] flex-shrink-0 mt-0.5" />
              <div className="text-sm text-[hsl(var(--danger))]">
                <p className="font-medium">Falha na instalação</p>
                <p className="text-xs mt-1 opacity-90">{job.error}</p>
              </div>
            </div>
          )}

          {isLoading && (
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <RefreshCw size={16} className="text-[hsl(var(--accent))] animate-spin" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-[hsl(var(--text))]">
                    {job ? PHASE_LABELS[job.phase] : 'Iniciando...'}
                  </p>
                  <div className="mt-2 h-1.5 w-full rounded-full bg-[hsl(var(--bg-subtle))] overflow-hidden">
                    <div
                      className={cn(
                        'h-full bg-[hsl(var(--accent))] transition-all',
                        job?.phase === 'ACQUIRING' && 'w-1/3',
                        job?.phase === 'VALIDATING' && 'w-2/3',
                        job?.phase === 'INSTALLING' && 'w-5/6',
                      )}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[hsl(var(--border-subtle))] flex items-center gap-2">
          {isDone && (
            <button
              onClick={() => {
                onSuccess()
                onClose()
              }}
              className={cn(
                'ml-auto px-4 py-2 rounded text-sm font-medium',
                'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))]',
                'hover:bg-[hsl(var(--accent)/0.2)] transition-colors',
              )}
            >
              Fechar
            </button>
          )}
          {isFailed && (
            <>
              <button
                onClick={onClose}
                className={cn(
                  'px-4 py-2 rounded text-sm font-medium',
                  'bg-[hsl(var(--bg-subtle))] text-[hsl(var(--text-muted))]',
                  'hover:bg-[hsl(var(--bg))] transition-colors',
                )}
              >
                Cancelar
              </button>
              <button
                onClick={handleRetry}
                disabled={isRetrying}
                className={cn(
                  'ml-auto px-4 py-2 rounded text-sm font-medium',
                  'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))]',
                  'hover:bg-[hsl(var(--accent)/0.2)] transition-colors',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                )}
              >
                {isRetrying ? 'Reiniciando...' : 'Tentar novamente'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
