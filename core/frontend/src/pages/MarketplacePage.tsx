import { useEffect, useState, useRef, useCallback } from 'react'
import {
  RefreshCw, Upload, Store, Download, LayoutGrid,
  CheckCircle2, ArrowUpCircle, AlertCircle,
} from 'lucide-react'
import { marketplaceApi, catalogApi, type CatalogListParams } from '@/lib/api'
import { PackageCard } from '@/components/marketplace/PackageCard'
import { PackageDetailPanel } from '@/components/marketplace/PackageDetailPanel'
import { OperationFeedback } from '@/components/marketplace/OperationFeedback'
import { CategorySidebar } from '@/components/catalog/CategorySidebar'
import { CatalogFilterBar } from '@/components/catalog/CatalogFilterBar'
import { CatalogCard } from '@/components/catalog/CatalogCard'
import { CatalogPagination } from '@/components/catalog/CatalogPagination'
import { InstallJobDialog } from '@/components/catalog/InstallJobDialog'
import { CatalogSourcesPanel } from '@/components/catalog/CatalogSourcesPanel'
import type { PackageInfo, OperationResponse, CatalogModule } from '@/types'
import { cn } from '@/lib/utils'

type Tab = 'installed' | 'available' | 'updates' | 'catalog'
type LoadState = 'idle' | 'loading' | 'success' | 'error'

interface Feedback { success: boolean; message: string; status?: string }

export function MarketplacePage() {
  const [tab,         setTab]         = useState<Tab>('installed')
  const [installed,   setInstalled]   = useState<PackageInfo[]>([])
  const [available,   setAvailable]   = useState<PackageInfo[]>([])
  const [updates,     setUpdates]     = useState<PackageInfo[]>([])
  const [loadState,   setLoadState]   = useState<LoadState>('idle')
  const [apiError,    setApiError]    = useState<string | null>(null)
  const [selected,    setSelected]    = useState<PackageInfo | null>(null)
  const [loadingPkg,  setLoadingPkg]  = useState<string | null>(null)
  const [feedback,    setFeedback]    = useState<Feedback | null>(null)
  const [importing,   setImporting]   = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  // Catalog state
  const [catalogModules,    setCatalogModules]    = useState<CatalogModule[]>([])
  const [catalogTotal,      setCatalogTotal]      = useState(0)
  const [catalogPage,       setCatalogPage]       = useState(1)
  const [catalogPageSize,   setCatalogPageSize]   = useState(24)
  const [catalogLoadState,  setCatalogLoadState]  = useState<LoadState>('idle')
  const [catalogError,      setCatalogError]      = useState<string | null>(null)
  const [catalogFilters,    setCatalogFilters]    = useState<Partial<CatalogListParams>>({})
  const [selectedCategory,  setSelectedCategory]  = useState<string | null>(null)
  const [selectedCatalog,   setSelectedCatalog]   = useState<CatalogModule | null>(null)
  const [installDialogModule, setInstallDialogModule] = useState<CatalogModule | null>(null)
  const [catalogConflicts,  setCatalogConflicts]  = useState<Record<string, string[]>>({})
  const [showSourcesPanel,  setShowSourcesPanel]  = useState(false)
  const [catalogLoadingPkg, setCatalogLoadingPkg] = useState<string | null>(null)

  const fetchAll = useCallback(async () => {
    setLoadState('loading')
    setApiError(null)
    try {
      const [ins, avail, upd] = await Promise.all([
        marketplaceApi.installed(),
        marketplaceApi.available(),
        marketplaceApi.updates(),
      ])
      setInstalled(ins)
      setAvailable(avail)
      setUpdates(upd)
      setLoadState('success')
    } catch (e) {
      setApiError(e instanceof Error ? e.message : 'Erro ao carregar')
      setLoadState('error')
    }
  }, [])

  const fetchCatalog = useCallback(async () => {
    setCatalogLoadState('loading')
    setCatalogError(null)
    try {
      const params: CatalogListParams = {
        ...catalogFilters,
        category: selectedCategory || undefined,
        page: catalogPage,
        page_size: catalogPageSize,
      }
      const res = await catalogApi.list(params)
      setCatalogModules(res.items)
      setCatalogTotal(res.total)
      setCatalogConflicts(res.conflicts)
      setCatalogLoadState('success')
    } catch (e) {
      setCatalogError(e instanceof Error ? e.message : 'Erro ao carregar catálogo')
      setCatalogLoadState('error')
    }
  }, [catalogFilters, selectedCategory, catalogPage, catalogPageSize])

  useEffect(() => { fetchAll() }, [fetchAll])

  useEffect(() => {
    if (tab === 'catalog') {
      fetchCatalog()
    }
  }, [tab, fetchCatalog])

  // auto-dismiss feedback after 4s
  useEffect(() => {
    if (!feedback) return
    const t = setTimeout(() => setFeedback(null), 4000)
    return () => clearTimeout(t)
  }, [feedback])

  const handleOperation = async (
    moduleId: string,
    op: () => Promise<OperationResponse>,
  ) => {
    setLoadingPkg(moduleId)
    try {
      const res = await op()
      setFeedback({ success: res.success, message: res.message, status: res.status })
      if (res.success) await fetchAll()
    } catch (e) {
      setFeedback({ success: false, message: e instanceof Error ? e.message : 'Erro' })
    } finally {
      setLoadingPkg(null)
    }
  }

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setImporting(true)
    try {
      const res = await marketplaceApi.importMod(file)
      setFeedback({ success: res.success, message: res.message, status: res.status })
      if (res.success) { await fetchAll(); setTab('installed') }
    } catch (err) {
      setFeedback({ success: false, message: err instanceof Error ? err.message : 'Import failed' })
    } finally {
      setImporting(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const packages = tab === 'installed' ? installed : tab === 'available' ? available : updates
  const isLoading = loadState === 'loading'

  const handleCatalogInstall = async (module: CatalogModule) => {
    if (module.source === 'local') {
      // Local source: use sync install from marketplace
      setCatalogLoadingPkg(module.module_id)
      try {
        const res = await marketplaceApi.install(module.module_id)
        setFeedback({ success: res.success, message: res.message, status: res.status })
        if (res.success) await fetchCatalog()
      } catch (e) {
        setFeedback({ success: false, message: e instanceof Error ? e.message : 'Erro na instalação' })
      } finally {
        setCatalogLoadingPkg(null)
      }
    } else {
      // Remote source: open install dialog with progress
      setInstallDialogModule(module)
    }
  }

  const TAB_CONFIG: { id: Tab; label: string; icon: typeof Store; count: number }[] = [
    { id: 'installed', label: 'Instalados',   icon: CheckCircle2,  count: installed.length },
    { id: 'available', label: 'Disponíveis',  icon: Download,      count: available.filter(p => !p.is_installed).length },
    { id: 'updates',   label: 'Atualizações', icon: ArrowUpCircle, count: updates.length   },
    { id: 'catalog',   label: 'Catálogo',     icon: LayoutGrid,    count: catalogTotal   },
  ]

  return (
    <div className="flex flex-col h-full">

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="px-6 pt-6 pb-0 flex-shrink-0">
        <div className="flex items-start justify-between gap-4 mb-5">
          <div>
            <h1 className="text-lg font-semibold text-[hsl(var(--text))] tracking-tight flex items-center gap-2">
              <Store size={17} className="text-[hsl(var(--accent))]" />
              Marketplace
            </h1>
            <p className="text-sm text-[hsl(var(--text-muted))] mt-0.5">
              Gerencie os módulos da plataforma
            </p>
          </div>

          <div className="flex items-center gap-2">
            {/* Import .mod */}
            <label className={cn(
              'inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium cursor-pointer',
              'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border))]',
              'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] hover:bg-[hsl(var(--bg-subtle))]',
              'transition-colors',
              importing && 'opacity-50 cursor-not-allowed',
            )}>
              {importing
                ? <RefreshCw size={12} className="animate-spin" />
                : <Upload size={12} />}
              Import .mod
              <input
                ref={fileRef}
                type="file"
                accept=".mod"
                className="hidden"
                disabled={importing}
                onChange={handleImport}
              />
            </label>

            {/* Refresh */}
            <button
              onClick={fetchAll}
              disabled={isLoading}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium',
                'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border))]',
                'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
                'hover:bg-[hsl(var(--bg-subtle))] transition-colors',
                'disabled:opacity-50 disabled:cursor-not-allowed',
              )}
            >
              <RefreshCw size={12} className={isLoading ? 'animate-spin' : ''} />
              Atualizar
            </button>
          </div>
        </div>

        {/* ── Tabs ───────────────────────────────────────────────────────── */}
        <div className="flex items-center gap-1 border-b border-[hsl(var(--border-subtle))]">
          {TAB_CONFIG.map(({ id, label, icon: Icon, count }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors relative',
                tab === id
                  ? 'text-[hsl(var(--text))] after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-[hsl(var(--accent))] after:rounded-full'
                  : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
              )}
            >
              <Icon size={12} />
              {label}
              {count > 0 && (
                <span className={cn(
                  'flex h-4 min-w-4 items-center justify-center rounded-full px-1 text-[10px] font-medium',
                  tab === id
                    ? 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))]'
                    : 'bg-[hsl(var(--bg-subtle))] text-[hsl(var(--text-muted))]',
                )}>
                  {count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* ── Error banner ───────────────────────────────────────────────── */}
      {loadState === 'error' && (
        <div className="mx-6 mt-4 flex items-center gap-2 px-4 py-2.5 rounded-lg
          border border-[hsl(var(--danger)/0.3)] bg-[hsl(var(--danger)/0.06)]
          text-sm text-[hsl(var(--danger))]">
          <AlertCircle size={14} className="flex-shrink-0" />
          <span>{apiError}</span>
        </div>
      )}

      {/* ── Package grid (Marketplace tabs) ─────────────────────────── */}
      {tab !== 'catalog' && (
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {isLoading && packages.length === 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {[1,2,3].map(i => (
                <div key={i} className="h-40 rounded-lg bg-[hsl(var(--bg-elevated))] animate-pulse border border-[hsl(var(--border-subtle))]" />
              ))}
            </div>
          ) : packages.length === 0 ? (
            <EmptyTab tab={tab} />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {packages.map(pkg => (
                <PackageCard
                  key={pkg.module_id}
                  pkg={pkg}
                  tab={tab}
                  loading={loadingPkg === pkg.module_id}
                  onClick={setSelected}
                  onInstall={p => handleOperation(p.module_id, () => marketplaceApi.install(p.module_id))}
                  onRemove={p  => {
                    if (window.confirm(
                      `Remover PERMANENTEMENTE o módulo "${p.name}"?\n` +
                      'Os arquivos do módulo serão apagados. Esta ação não pode ser desfeita.'
                    )) {
                      handleOperation(p.module_id, () => marketplaceApi.remove(p.module_id));
                    }
                  }}
                  onUpdate={p  => handleOperation(p.module_id, () => marketplaceApi.update(p.module_id))}
                  onActivate={p   => handleOperation(p.module_id, () => marketplaceApi.activate(p.module_id))}
                  onDeactivate={p => handleOperation(p.module_id, () => marketplaceApi.deactivate(p.module_id))}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Catalog tab (3-zone layout) ───────────────────────────────── */}
      {tab === 'catalog' && (
        <>
          <div className="flex-1 overflow-hidden flex flex-col">
            {/* Filter bar */}
            <CatalogFilterBar
              onChange={filters => {
                setCatalogFilters(filters)
                setCatalogPage(1)
              }}
            />

            {/* Main content area */}
            <div className="flex-1 overflow-hidden flex">
              {/* Sidebar */}
              <CategorySidebar
                selected={selectedCategory}
                onSelect={category => {
                  setSelectedCategory(category)
                  setCatalogPage(1)
                }}
                loading={catalogLoadState === 'loading'}
              />

              {/* Grid + Pagination */}
              <div className="flex-1 flex flex-col overflow-hidden">
                {/* Error banner */}
                {catalogLoadState === 'error' && (
                  <div className="mx-4 mt-4 flex items-center gap-2 px-4 py-2.5 rounded-lg
                    border border-[hsl(var(--danger)/0.3)] bg-[hsl(var(--danger)/0.06)]
                    text-sm text-[hsl(var(--danger))]">
                    <AlertCircle size={14} className="flex-shrink-0" />
                    <span>{catalogError}</span>
                  </div>
                )}

                {/* Grid */}
                <div className="flex-1 overflow-y-auto px-6 py-5">
                  {catalogLoadState === 'loading' && catalogModules.length === 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      {[1,2,3,4,5,6].map(i => (
                        <div key={i} className="h-40 rounded-lg bg-[hsl(var(--bg-elevated))] animate-pulse border border-[hsl(var(--border-subtle))]" />
                      ))}
                    </div>
                  ) : catalogModules.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 text-center">
                      <div className="w-12 h-12 rounded-xl bg-[hsl(var(--bg-subtle))] flex items-center justify-center mb-4">
                        <Store size={20} className="text-[hsl(var(--text-muted))]" />
                      </div>
                      <p className="text-sm font-medium text-[hsl(var(--text))] mb-1">Nenhum módulo encontrado</p>
                      <p className="text-xs text-[hsl(var(--text-muted))] max-w-xs">Tente ajustar os filtros ou adicionar novas fontes</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      {catalogModules.map(mod => (
                        <CatalogCard
                          key={mod.module_id}
                          module={mod}
                          conflictCount={catalogConflicts[mod.module_id]?.length}
                          loading={catalogLoadingPkg === mod.module_id}
                          onClick={setSelectedCatalog}
                          onInstall={handleCatalogInstall}
                        />
                      ))}
                    </div>
                  )}
                </div>

                {/* Pagination */}
                {catalogModules.length > 0 && (
                  <CatalogPagination
                    page={catalogPage}
                    pageSize={catalogPageSize}
                    total={catalogTotal}
                    onPageChange={setCatalogPage}
                    onPageSizeChange={size => {
                      setCatalogPageSize(size)
                      setCatalogPage(1)
                    }}
                  />
                )}
              </div>
            </div>
          </div>

          {/* Toolbar button for sources panel */}
          <div className="px-6 py-4 border-t border-[hsl(var(--border-subtle))] flex gap-2">
            <button
              onClick={() => setShowSourcesPanel(true)}
              className={cn(
                'inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium',
                'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border))]',
                'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] hover:bg-[hsl(var(--bg-subtle))]',
                'transition-colors',
              )}
            >
              Gerenciar fontes
            </button>
          </div>
        </>
      )}

      {/* ── Detail panel (Marketplace) ────────────────────────────────── */}
      {selected && (
        <PackageDetailPanel pkg={selected} onClose={() => setSelected(null)} />
      )}

      {/* ── Detail panel (Catalog) ────────────────────────────────────── */}
      {selectedCatalog && tab === 'catalog' && (
        <PackageDetailPanel
          pkg={{
            ...selectedCatalog,
            is_enabled: selectedCatalog.is_installed,
            icon: null,
            color: null,
            order: null,
            signature: null,
          } as PackageInfo}
          onClose={() => setSelectedCatalog(null)}
        />
      )}

      {/* ── Install dialog (remote sources) ───────────────────────────── */}
      {installDialogModule && (
        <InstallJobDialog
          moduleId={installDialogModule.module_id}
          moduleName={installDialogModule.name}
          onClose={() => setInstallDialogModule(null)}
          onSuccess={() => {
            fetchCatalog()
            fetchAll()
          }}
        />
      )}

      {/* ── Sources panel ─────────────────────────────────────────────── */}
      {showSourcesPanel && (
        <CatalogSourcesPanel
          onClose={() => setShowSourcesPanel(false)}
          onRefresh={() => fetchCatalog()}
        />
      )}

      {/* ── Operation feedback toast ────────────────────────────────────── */}
      {feedback && (
        <OperationFeedback
          success={feedback.success}
          message={feedback.message}
          status={feedback.status}
          onDismiss={() => setFeedback(null)}
        />
      )}
    </div>
  )
}

// ── Empty states per tab ──────────────────────────────────────────────────────
function EmptyTab({ tab }: { tab: Tab }) {
  const msgs: Record<Tab, { title: string; desc: string }> = {
    installed: {
      title: 'Nenhum módulo instalado',
      desc:  'Instale módulos da aba Disponíveis ou importe um arquivo .mod.',
    },
    available: {
      title: 'Repositório vazio',
      desc:  'Coloque arquivos .mod em modules/repository/ ou use "Import .mod".',
    },
    updates: {
      title: 'Tudo atualizado',
      desc:  'Todos os módulos instalados estão na versão mais recente.',
    },
    catalog: {
      title: 'Nenhum módulo encontrado',
      desc:  'Tente ajustar os filtros ou adicionar novas fontes.',
    },
  }
  const { title, desc } = msgs[tab]
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="w-12 h-12 rounded-xl bg-[hsl(var(--bg-subtle))] flex items-center justify-center mb-4">
        <Store size={20} className="text-[hsl(var(--text-muted))]" />
      </div>
      <p className="text-sm font-medium text-[hsl(var(--text))] mb-1">{title}</p>
      <p className="text-xs text-[hsl(var(--text-muted))] max-w-xs">{desc}</p>
    </div>
  )
}
