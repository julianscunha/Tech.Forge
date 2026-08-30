import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'
import { diagnosticsApi } from '@/lib/api'
import { StatCard } from '@/components/ui/StatCard'

export function ModuleFailuresCard() {
  const navigate = useNavigate()
  const [count, setCount] = useState<number | null>(null)

  useEffect(() => {
    diagnosticsApi.errors(50)
      .then((errors) => setCount(errors.filter((e) => e.source === 'execution').length))
      .catch(() => setCount(null))
  }, [])

  return (
    <button onClick={() => navigate('/diagnostics')} className="text-left w-full h-full">
      <StatCard
        label="Module Failures"
        value={count ?? '—'}
        icon={AlertTriangle}
        description="Falhas de execução recentes"
      />
    </button>
  )
}
