import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Link2Off } from 'lucide-react'
import { dependenciesApi } from '@/lib/api'
import { StatCard } from '@/components/ui/StatCard'

export function BlockedDependenciesCard() {
  const navigate = useNavigate()
  const [count, setCount] = useState<number | null>(null)

  useEffect(() => {
    dependenciesApi.validateAll()
      .then((report) => {
        const blocked = Object.values(report)
          .filter((checks) => checks.some((c) => c.required && !c.passed))
        setCount(blocked.length)
      })
      .catch(() => setCount(null))
  }, [])

  return (
    <button onClick={() => navigate('/diagnostics')} className="text-left w-full h-full">
      <StatCard
        label="Blocked Dependencies"
        value={count ?? '—'}
        icon={Link2Off}
        description="Módulos com dependência obrigatória não satisfeita"
      />
    </button>
  )
}
