import { useEffect, useState, useCallback } from 'react'
import {
  Boxes, RefreshCw, AlertCircle, Terminal,
  ToggleLeft, ToggleRight, Search,
} from 'lucide-react'
import { registryApi, completenessApi, moduleTrustApi } from '@/lib/api'
import { useDevModeStore } from '@/store/devmode'
import { ModuleCard } from '@/components/modules/ModuleCard'
import { ModuleDetailPanel } from '@/components/modules/ModuleDetailPanel'
import { LoaderJournalViewer } from '@/components/modules/LoaderJournalViewer'
import type { ModuleEntry, LoaderResult, ModuleStatus, CompletenessReport, ModuleTrust } from '@/types'
import { cn } from '@/lib/utils'

type LoadState = 'idle' | 'loading' | 'success' | 'error'

const STATUS_FILTERS: { value: ModuleStatus | 'ALL'; label: string }[] = [
  { value: 'ALL',         label: 'Todos'         },
  { value: 'INSTALLED',   label: 'Instalados'    },
  { value: 'DISABLED',    label: 'Desabilitados' },
  { value: 'INVALID',     label: 'Inválidos'     },
  { value: 'INCOMPATIBLE', label: 'Incompatíveis' },
]

const STATUS_LABEL: Record<string, string> = {
  INSTALLED: 'Instalados',
  DISABLED: 'Desabilitados',
  INVALID: 'Inválidos',
  INCOMPATIBLE: 'Incompatíveis',
}

export function ModulesPage() {
  const { developerMode, toggleDeveloperMode } = useDevModeStore()

  const [modules, setModules]           = useState<ModuleEntry[]>([])
  const [journal, setJournal]           = useState<LoaderResult | null>(null)
  const [completeness, setCompleteness] = useState<Record<string, CompletenessReport>>({})
  const [moduleTrust, setModuleTrust]   = useState<Record<string, ModuleTrust>>({})
  const [loadState, setLoadState]       = useState<LoadState>('idle')
  const [error, setError]               = useState<string | null>(null)
  const [selected, setSelected]         = useState<ModuleEntry | null>(null)
  const [statusFilter, setStatusFilter] = useState<ModuleStatus | 'ALL'>('ALL')
  const [search, setSearch]             = useState('')
  const [showJournal, setShowJournal]   = useState(false)

  const fetchAll = useCallback(async () => {
    setLoadState('loading')
    setError(null)
    try {
      const [mods, j, comp, trust] = await Promise.all([
        registryApi.listModules(developerMode),
        registryApi.getLoaderJournal().catch(() => null),
        completenessApi.all().catch(() => [] as CompletenessReport[]),
        moduleTrustApi.list().catch(() => [] as ModuleTrust[]),
      ])
      setModules(mods)
      setJournal(j)
      setCompleteness(Object.fromEntries(comp.map(c => [c.module_id, c])))
      setModuleTrust(Object.fromEntries(trust.map(t => [t.module_id, t])))
      setLoadState('success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido')
      setLoadState('error')
    }
  }, [developerMode])

  useEffect(() => { fetchAll() }, [fetchAll])

  // Re-fetch when developer mode changes (manifest_raw is included or stripped)
  useEffect(() => {
    if (loadState === 'success') fetchAll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [developerMode])

  const filtered = modules.filter((m) => {
    const matchStatus = statusFilter === 'ALL' || m.status === statusFilter
    const q = search.toLowerCase()
    const matchSearch =
      !q ||
      m.name.toLowerCase().includes(q) ||
      m.category.toLowerCase().includes(q) ||
      m.vendor.toLowerCase().includes(q) ||
      m.module_id.toLowerCase().includes(q)
    return matchStatus && matchSearch
  })

  const counts = {
    INSTALLED:    modules.filter((m) => m.status === 'INSTALLED').length,
    DISABLED:     modules.filter((m) => m.status === 'DISABLED').length,
    INVALID:      modules.filter((m) => m.status === 'INVALID').length,
    INCOMPATIBLE: modules.filter((m) => m.status === 'INCOMPATIBLE').length,
  }

  return (
    <div className="flex flex-col h-full">
      {/* ── Page header ────────────────────────────────────────────────── */}
      <div className="px-6 pt-4 pb-4 flex-shrink-0">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-lg font-semibold text-[hsl(var(--text))] tracking-tight flex items-center gap-2">
              <Boxes size={17} className="text-[hsl(var(--accent))]" />
              Módulos
            </h1>
            <p className="text-sm text-[hsl(var(--text-muted))] mt-0.5">
              {modules.length} módulo{modules.length !== 1 ? 's' : ''} no registry
            </p>
          </div>

          <div className="flex items-center gap-2">
            {/* Developer Mode toggle */}
            <button
              onClick={toggleDeveloperMode}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded text-xs font-medium transition-colors',
                developerMode
                  ? 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))]'
                  : 'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border))] text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]'
              )}
            >
              {developerMode
                ? <ToggleRight size={13} />
                : <ToggleLeft  size={13} />}
              Developer Mode
            </button>

            {/* Refresh */}
            <button
              onClick={fetchAll}
              disabled={loadState === 'loading'}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium',
                'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border))]',
                'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
                'hover:bg-[hsl(var(--bg-subtle))] transition-colors',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              <RefreshCw size={12} className={loadState === 'loading' ? 'animate-spin' : ''} />
              Atualizar
            </button>
          </div>
        </div>

        {/* ── Stats strip ──────────────────────────────────────────────── */}
        <div className="flex items-center gap-3 mt-4">
          {Object.entries(counts).map(([status, count]) => (
            <div key={status}
              className="flex items-center gap-1.5 text-xs">
              <span className={cn('w-1.5 h-1.5 rounded-full',
                status === 'INSTALLED'   && 'bg-[hsl(var(--success))]',
                status === 'DISABLED'    && 'bg-[hsl(var(--text-subtle))]',
                status === 'INVALID'     && 'bg-[hsl(var(--danger))]',
                status === 'INCOMPATIBLE' && 'bg-[hsl(var(--warning))]',
              )} />
              <span className="text-[hsl(var(--text-muted))]">{STATUS_LABEL[status] ?? status}</span>
              <span className="font-mono font-semibold text-[hsl(var(--text))]">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Toolbar ────────────────────────────────────────────────────── */}
      <div className="px-6 pb-4 flex-shrink-0 flex items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 max-w-xs">
          <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-subtle))]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Pesquisar módulos…"
            className={cn(
              'w-full pl-7 pr-3 py-1.5 rounded text-xs',
              'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border-subtle))]',
              'text-[hsl(var(--text))] placeholder-[hsl(var(--text-subtle))]',
              'focus:outline-none focus:border-[hsl(var(--accent)/0.5)]',
              'transition-colors'
            )}
          />
        </div>

        {/* Status filter */}
        <div className="flex items-center gap-1">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setStatusFilter(f.value)}
              className={cn(
                'px-2.5 py-1 rounded text-xs font-medium transition-colors',
                statusFilter === f.value
                  ? 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))]'
                  : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] hover:bg-[hsl(var(--bg-subtle))]'
              )}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Developer Mode — Journal toggle */}
        {developerMode && journal && (
          <button
            onClick={() => setShowJournal((v) => !v)}
            className={cn(
              'ml-auto flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium',
              showJournal
                ? 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))]'
                : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] hover:bg-[hsl(var(--bg-subtle))]'
            )}
          >
            <Terminal size={11} />
            Loading Journal
          </button>
        )}
      </div>

      {/* ── Error banner ───────────────────────────────────────────────── */}
      {loadState === 'error' && (
        <div className="mx-6 mb-4 flex items-center gap-2 px-4 py-2.5 rounded-lg
          border border-[hsl(var(--danger)/0.3)] bg-[hsl(var(--danger)/0.06)]
          text-sm text-[hsl(var(--danger))]">
          <AlertCircle size={14} className="flex-shrink-0" />
          <span>Não foi possível conectar ao backend. {error}</span>
        </div>
      )}

      {/* ── Loader Journal (Developer Mode) ────────────────────────────── */}
      {developerMode && showJournal && journal && (
        <div className="px-6 mb-4 flex-shrink-0">
          <LoaderJournalViewer result={journal} />
        </div>
      )}

      {/* ── Module grid ────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-6 pb-6">
        {loadState === 'loading' && modules.length === 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-32 rounded-lg bg-[hsl(var(--bg-elevated))] animate-pulse border border-[hsl(var(--border-subtle))]" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            modules={modules}
            search={search}
            statusFilter={statusFilter}
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {filtered.map((m) => (
              <ModuleCard
                key={m.module_id}
                module={m}
                developerMode={developerMode}
                completeness={completeness[m.module_id]}
                trust={moduleTrust[m.module_id]}
                onClick={setSelected}
              />
            ))}
          </div>
        )}
      </div>

      {/* ── Detail panel ───────────────────────────────────────────────── */}
      {selected && (
        <ModuleDetailPanel
          module={selected}
          developerMode={developerMode}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  )
}

// ── Empty state ───────────────────────────────────────────────────────────────

function EmptyState({
  modules,
  search,
  statusFilter,
}: {
  modules: ModuleEntry[]
  search: string
  statusFilter: string
}) {
  const isFiltered = search || statusFilter !== 'ALL'

  if (modules.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-12 h-12 rounded-xl bg-[hsl(var(--bg-subtle))] flex items-center justify-center mb-4">
          <Boxes size={20} className="text-[hsl(var(--text-muted))]" />
        </div>
        <p className="text-sm font-medium text-[hsl(var(--text))] mb-1">Nenhum módulo encontrado</p>
        <p className="text-xs text-[hsl(var(--text-muted))] max-w-xs">
          Coloque módulos em <code className="font-mono text-[hsl(var(--accent))]">modules/installed/</code> e reinicie o backend.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <p className="text-sm text-[hsl(var(--text-muted))]">
        {isFiltered ? 'Nenhum módulo corresponde aos filtros.' : 'Nenhum módulo para exibir.'}
      </p>
    </div>
  )
}
