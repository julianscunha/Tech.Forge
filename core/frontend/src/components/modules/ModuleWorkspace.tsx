import { useLocation } from 'react-router-dom'
import { ModuleHost } from '@/pages/ModuleHost'
import { isModuleRoute } from '@/lib/moduleRoute'
import { useModuleTabsStore } from '@/store/moduleTabs'

/**
 * Renderiza TODAS as abas de módulo abertas ao mesmo tempo — cada uma numa
 * instância própria de `ModuleHost`, escondida via CSS quando não é a ativa.
 * Nunca desmonta uma aba por navegação: é isso que preserva o estado do
 * módulo (formulário, scroll, o que for) ao trocar de módulo e voltar.
 *
 * Montado uma vez em `AppShell`, fora do `<Outlet/>` — sobrevive a qualquer
 * troca de rota. Só fica visível quando a rota atual é `/modules/:id`.
 */
export function ModuleWorkspace() {
  const location = useLocation()
  const tabs = useModuleTabsStore((s) => s.tabs)
  const activeId = useModuleTabsStore((s) => s.activeId)

  if (tabs.length === 0) return null // nada aberto ainda — nada a preservar

  return (
    <div className="h-full" style={{ display: isModuleRoute(location.pathname) ? 'block' : 'none' }}>
      {tabs.map((tab) => (
        <div key={tab.id} className="h-full" style={{ display: tab.id === activeId ? 'block' : 'none' }}>
          <ModuleHost moduleId={tab.id} />
        </div>
      ))}
    </div>
  )
}
