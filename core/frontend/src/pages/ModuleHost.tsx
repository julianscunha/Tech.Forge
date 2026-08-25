/**
 * ModuleHost — Phase 2+/3
 * =======================
 * Host page for dynamically loaded modules. Rendered at
 * /modules/:moduleId/* by the Plugin Loader route in AppRouter.
 *
 * Phase 3 (Fase 3 §11): if the module declares `entry_frontend`, the host
 * dynamically imports it from /modules/<id>/assets/<entry_frontend> and
 * renders the exported default component INSIDE the App Shell content area.
 * Failure to load falls back to the metadata view — never breaks the platform.
 */
import { useEffect, useState, Suspense, type ComponentType } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Puzzle, ArrowLeft, ExternalLink, AlertTriangle } from 'lucide-react'
import { registryApi } from '@/lib/api'
import type { ModuleEntry } from '@/types'
import { cn } from '@/lib/utils'

const _loadedModules = new Map<string, ComponentType>()

/** Dynamically import a module's entry_frontend as a React component. */
async function loadModuleComponent(
  moduleId: string,
  entryFrontend?: string | null,
): Promise<ComponentType | null> {
  if (!entryFrontend) return null
  const cacheKey = `${moduleId}:${entryFrontend}`
  if (_loadedModules.has(cacheKey)) return _loadedModules.get(cacheKey)!
  if (!/\.(js|mjs)$/i.test(entryFrontend)) return null // compiled JS only

  const url = `/api/v1/modules/${moduleId}/assets/${entryFrontend.replace(/^\//, '')}`
  const mod = await import(/* @vite-ignore */ /* webpackIgnore: true */ url)
  const Component = (mod.default ?? null) as ComponentType | null
  if (Component) _loadedModules.set(cacheKey, Component)
  return Component
}

export function ModuleHost() {
  const { moduleId } = useParams<{ moduleId: string }>()
  const [entry, setEntry] = useState<ModuleEntry | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [ModuleComponent, setModuleComponent] = useState<ComponentType | null>(null)
  const [moduleLoadError, setModuleLoadError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setModuleComponent(null)
    setModuleLoadError(null)

    if (!moduleId) {
      setError('Módulo não especificado.')
      setLoading(false)
      return
    }

    registryApi
      .getModule(moduleId)
      .then(async (e) => {
        if (cancelled) return
        setEntry(e)
        try {
          const comp = await loadModuleComponent(moduleId, e.entry_frontend)
          if (!cancelled) setModuleComponent(comp)
        } catch (err) {
          if (!cancelled) {
            setModuleLoadError(
              err instanceof Error ? err.message : 'Falha ao carregar interface do módulo.',
            )
          }
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Falha ao carregar módulo.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [moduleId])

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <p className="text-sm text-[hsl(var(--text-subtle))]">Carregando módulo…</p>
      </div>
    )
  }

  if (error || !entry) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 p-8">
        <Puzzle size={32} className="text-[hsl(var(--text-subtle))]" />
        <p className="text-sm text-[hsl(var(--text-muted))]">
          {error ?? 'Módulo não encontrado.'}
        </p>
        <Link
          to="/modules"
          className="text-xs text-[hsl(var(--accent))] hover:underline inline-flex items-center gap-1"
        >
          <ArrowLeft size={12} /> Voltar para Módulos
        </Link>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[hsl(var(--accent-muted))] flex items-center justify-center flex-shrink-0">
            <Puzzle size={18} className="text-[hsl(var(--accent))]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-[hsl(var(--text))]">{entry.name}</h2>
              <span
                className={cn(
                  'px-1.5 py-0.5 rounded text-[10px] font-mono',
                  'bg-[hsl(var(--bg-subtle))] text-[hsl(var(--text-muted))]',
                )}
              >
                v{entry.version}
              </span>
            </div>
            <p className="text-xs text-[hsl(var(--text-muted))]">{entry.description}</p>
          </div>
        </div>
        <Link
          to="/modules"
          className="inline-flex items-center gap-1 text-xs text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]"
        >
          <ArrowLeft size={12} /> Módulos
        </Link>
      </div>

      {/* Module UI — dynamic import of entry_frontend (Fase 3 §11) */}
      {ModuleComponent ? (
        <Suspense
          fallback={
            <p className="text-xs text-[hsl(var(--text-subtle))]">Carregando interface…</p>
          }
        >
          <ModuleComponent />
        </Suspense>
      ) : (
        moduleLoadError && (
          <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 flex items-start gap-2">
            <AlertTriangle size={14} className="text-amber-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs font-medium text-amber-500">Interface do módulo indisponível</p>
              <p className="text-[11px] text-[hsl(var(--text-muted))] mt-0.5">{moduleLoadError}</p>
            </div>
          </div>
        )
      )}

      {/* Metadata */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          ['Categoria', entry.category],
          ['Vendor', entry.vendor],
          ['Autor', entry.author],
          ['Status', entry.status],
        ].map(([label, value]) => (
          <div key={label} className="rounded-lg border border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-elevated))] p-3">
            <p className="text-[10px] uppercase tracking-widest text-[hsl(var(--text-subtle))]">{label}</p>
            <p className="text-sm text-[hsl(var(--text))] mt-0.5 truncate">{value}</p>
          </div>
        ))}
      </div>

      {/* Backend API probe — mounted by the Plugin Loader under /api/v1/modules/<id> */}
      <div className="rounded-lg border border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-elevated))] p-4 space-y-3">
        <p className="text-xs font-medium text-[hsl(var(--text-muted))]">
          API do módulo <span className="font-mono text-[hsl(var(--text-subtle))]">/api/v1/modules/{moduleId}</span>
        </p>
        <BackendProbe moduleId={moduleId!} />
      </div>
    </div>
  )
}

function BackendProbe({ moduleId }: { moduleId: string }) {
  const [result, setResult] = useState<string | null>(null)
  const [ok, setOk] = useState<boolean | null>(null)

  const ping = () => {
    fetch(`/api/v1/modules/${moduleId}/ping`)
      .then(async (r) => {
        setOk(r.ok)
        setResult(await r.text())
      })
      .catch((e) => {
        setOk(false)
        setResult(String(e))
      })
  }

  return (
    <div className="space-y-2">
      <button
        onClick={ping}
        className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium bg-[hsl(var(--accent))] text-white hover:opacity-90 transition-opacity"
      >
        <ExternalLink size={12} /> Testar GET /ping
      </button>
      {ok !== null && (
        <pre
          className={cn(
            'rounded p-2.5 text-xs font-mono whitespace-pre-wrap break-all',
            ok
              ? 'bg-green-500/10 text-green-500'
              : 'bg-red-500/10 text-red-500',
          )}
        >
          {result}
        </pre>
      )}
    </div>
  )
}
