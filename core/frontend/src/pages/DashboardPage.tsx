import { useEffect, useState } from 'react'
import { Boxes, LayoutGrid, LayoutDashboard, Server, Database, RefreshCw, AlertCircle, Plug } from 'lucide-react'
import { platformApi, servicesApi } from '@/lib/api'
import { StatCard } from '@/components/ui/StatCard'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { DraggableCard } from '@/components/dashboard/DraggableCard'
import { CardVisibilityMenu } from '@/components/dashboard/CardVisibilityMenu'
import { ModuleFailuresCard } from '@/components/dashboard/ModuleFailuresCard'
import { BlockedDependenciesCard } from '@/components/dashboard/BlockedDependenciesCard'
import { RecentCriticalEventsCard } from '@/components/dashboard/RecentCriticalEventsCard'
import { ResourceUsageCard } from '@/components/dashboard/ResourceUsageCard'
import { HeaviestModuleCard } from '@/components/dashboard/HeaviestModuleCard'
import { useDashboardLayoutStore, getEffectiveOrder, type DashboardCardId } from '@/store/dashboardLayout'
import type { PlatformStatus } from '@/types'
import { cn } from '@/lib/utils'

type LoadState = 'idle' | 'loading' | 'success' | 'error'

export function DashboardPage() {
  const [status, setStatus] = useState<PlatformStatus | null>(null)
  const [loadState, setLoadState] = useState<LoadState>('idle')
  const [error, setError] = useState<string | null>(null)
  const [serviceCounts, setServiceCounts] = useState<{ active: number; unavailable: number } | null>(null)
  const { order, hidden } = useDashboardLayoutStore()

  const fetchStatus = async () => {
    setLoadState('loading')
    setError(null)
    try {
      const data = await platformApi.getStatus()
      setStatus(data)
      setLoadState('success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido')
      setLoadState('error')
    }
    try {
      const services = await servicesApi.list()
      setServiceCounts({
        active: services.filter(s => s.status === 'ACTIVE').length,
        unavailable: services.filter(s => s.status !== 'ACTIVE').length,
      })
    } catch { setServiceCounts(null) }
  }

  useEffect(() => {
    fetchStatus()
  }, [])

  const cardRenderers: Record<DashboardCardId, React.ReactNode> = {
    'modules-installed': (
      <StatCard
        label="Módulos Instalados"
        value={status?.modules_installed ?? '—'}
        icon={Boxes}
        description={status ? `${status.modules_enabled} habilitados` : undefined}
      />
    ),
    'modules-active': (
      <StatCard label="Módulos Ativos" value={status?.modules_enabled ?? '—'} icon={Boxes} />
    ),
    'categories': (
      <StatCard
        label="Categorias"
        value={status?.categories_registered ?? '—'}
        icon={LayoutGrid}
        description="Registradas no core"
      />
    ),
    'services-active': serviceCounts ? (
      <StatCard
        label="Serviços Ativos"
        value={serviceCounts.active}
        icon={Plug}
        description={serviceCounts.unavailable > 0 ? `${serviceCounts.unavailable} indisponível(is)` : undefined}
      />
    ) : <StatCard label="Serviços Ativos" value="—" icon={Plug} />,
    'module-failures': <ModuleFailuresCard />,
    'blocked-dependencies': <BlockedDependenciesCard />,
    'recent-events': <RecentCriticalEventsCard />,
    'resource-usage': <ResourceUsageCard />,
    'heaviest-module': <HeaviestModuleCard />,
  }

  const visibleOrder = getEffectiveOrder(order).filter((id) => !hidden.includes(id))

  return (
    <div className="px-6 pt-4 pb-6 space-y-6 max-w-7xl">
      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-lg font-semibold text-[hsl(var(--text))] tracking-tight flex items-center gap-2">
            <LayoutDashboard size={17} className="text-[hsl(var(--accent))]" />
            Dashboard
          </h1>
          <p className="text-sm text-[hsl(var(--text-muted))] mt-0.5">
            Estado atual da plataforma
          </p>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={fetchStatus}
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
          <CardVisibilityMenu />
        </div>
      </div>

      {/* Platform identity */}
      {status && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg border border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-elevated))]">
          <div className="w-8 h-8 rounded-md bg-[hsl(var(--accent))] flex items-center justify-center flex-shrink-0">
            <span className="text-white text-xs font-bold">TF</span>
          </div>
          <div>
            <p className="text-sm font-semibold text-[hsl(var(--text))]">
              {status.platform_name}
            </p>
            <p className="text-xs text-[hsl(var(--text-muted))] font-mono">
              v{status.platform_version}
            </p>
          </div>
        </div>
      )}

      {/* Error state */}
      {loadState === 'error' && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-lg border border-[hsl(var(--danger)/0.3)] bg-[hsl(var(--danger)/0.06)] text-sm text-[hsl(var(--danger))]">
          <AlertCircle size={14} className="flex-shrink-0" />
          <span>Não foi possível conectar ao backend. {error}</span>
        </div>
      )}

      {/* Status row */}
      {(loadState === 'success' || loadState === 'loading') && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="rounded-lg px-4 py-3 border border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-elevated))]">
              <p className="text-xs text-[hsl(var(--text-muted))] mb-1.5 uppercase tracking-wide font-medium flex items-center gap-1.5">
                <Server size={11} />
                Backend
              </p>
              {status ? (
                <StatusBadge status={status.backend_status} />
              ) : (
                <Skeleton className="h-4 w-16" />
              )}
            </div>

            <div className="rounded-lg px-4 py-3 border border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-elevated))]">
              <p className="text-xs text-[hsl(var(--text-muted))] mb-1.5 uppercase tracking-wide font-medium flex items-center gap-1.5">
                <Database size={11} />
                Banco de Dados
              </p>
              {status ? (
                <StatusBadge status={status.database_status} />
              ) : (
                <Skeleton className="h-4 w-16" />
              )}
            </div>
          </div>

          {/* Cards personalizáveis — arrastar pra reordenar, engrenagem pra mostrar/ocultar */}
          {visibleOrder.length === 0 ? (
            <p className="text-xs text-[hsl(var(--text-subtle))] text-center py-8">
              Nenhum card visível — use a engrenagem acima pra mostrar algum.
            </p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 items-start">
              {visibleOrder.map((id) => (
                <DraggableCard key={id} id={id}>
                  {cardRenderers[id]}
                </DraggableCard>
              ))}
            </div>
          )}
        </>
      )}

      {/* Skeleton on first load */}
      {loadState === 'idle' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-[104px] rounded-lg" />
          ))}
        </div>
      )}
    </div>
  )
}

// ── Mini skeleton ─────────────────────────────────────────────────────────────
function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'rounded bg-[hsl(var(--bg-subtle))] animate-pulse',
        className
      )}
    />
  )
}
