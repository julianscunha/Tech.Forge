import { useEffect, useState } from 'react'
import { HardDrive } from 'lucide-react'
import { diagnosticsApi } from '@/lib/api'
import { formatBytes } from '@/lib/utils'
import { StatCard } from '@/components/ui/StatCard'
import type { HeaviestModule } from '@/types'

export function HeaviestModuleCard() {
  const [top, setTop] = useState<HeaviestModule | null | undefined>(undefined)

  useEffect(() => {
    diagnosticsApi.heaviestModules(1)
      .then((mods) => setTop(mods[0] ?? null))
      .catch(() => setTop(null))
  }, [])

  return (
    <StatCard
      label="Módulo mais pesado"
      value={top === undefined ? '—' : top ? formatBytes(top.disk_bytes) : '—'}
      icon={HardDrive}
      description={
        top === undefined ? undefined
        : top ? `${top.module_id} · falhas ${(top.failure_rate * 100).toFixed(0)}%`
        : 'Sem execuções registradas ainda'
      }
    />
  )
}
