import { Settings } from 'lucide-react'
import { ComingSoon } from '@/components/ui/ComingSoon'

export function SettingsPage() {
  return (
    <ComingSoon
      icon={Settings}
      title="Configurações"
      description="Configurações globais da plataforma. Disponível em versão futura."
      phase="Em breve"
    />
  )
}
