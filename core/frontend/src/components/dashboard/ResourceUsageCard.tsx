import { useEffect, useState } from 'react'
import { Cpu, ChevronDown } from 'lucide-react'
import { diagnosticsApi } from '@/lib/api'
import { formatBytes, cn } from '@/lib/utils'
import { MiniBar, MiniPie } from './MiniCharts'
import type { ResourceUsage } from '@/types'

const REFRESH_MS = 20_000

export function ResourceUsageCard() {
  const [data, setData] = useState<ResourceUsage | null>(null)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    let cancelled = false
    const load = () => diagnosticsApi.resources().then((d) => { if (!cancelled) setData(d) }).catch(() => {})
    load()
    const interval = setInterval(load, REFRESH_MS)
    return () => { cancelled = true; clearInterval(interval) }
  }, [])

  const diskPercent = data ? (data.disk_used_bytes / data.disk_total_bytes) * 100 : 0

  return (
    <div className="rounded-lg bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border-subtle))] overflow-hidden h-full">
      <button
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="w-full text-left p-4 h-[104px]"
      >
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-xs text-[hsl(var(--text-muted))] font-medium uppercase tracking-wide flex items-center gap-1">
              Recursos
              <ChevronDown size={11} className={cn('transition-transform', expanded && 'rotate-180')} />
            </p>
            <p className="text-2xl font-semibold text-[hsl(var(--text))] font-mono tabular-nums">
              {data ? `${data.cpu_percent.toFixed(0)}%` : '—'}
            </p>
            <p className="text-xs text-[hsl(var(--text-subtle))]">
              CPU · {data ? formatBytes(data.memory_rss_bytes) : '—'} RAM
            </p>
          </div>
          <div className="w-8 h-8 rounded-md bg-[hsl(var(--accent-muted))] flex items-center justify-center flex-shrink-0">
            <Cpu size={15} className="text-[hsl(var(--accent))]" />
          </div>
        </div>
      </button>

      {expanded && data && (
        <div className="px-4 pb-4 pt-1 border-t border-[hsl(var(--border-subtle))] space-y-3">
          <MiniBar label="CPU" percent={data.cpu_percent} valueLabel={`${data.cpu_percent.toFixed(0)}%`} />
          <MiniPie
            usedPercent={diskPercent}
            label={`Disco: ${formatBytes(data.disk_used_bytes)} / ${formatBytes(data.disk_total_bytes)}`}
          />
          <p className="text-[10px] text-[hsl(var(--text-subtle))]">Atualiza a cada 20s</p>
        </div>
      )}
    </div>
  )
}
