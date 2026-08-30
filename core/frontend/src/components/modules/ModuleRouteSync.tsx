import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { registryApi } from '@/lib/api'
import { useModuleTabsStore } from '@/store/moduleTabs'

/**
 * Rota `/modules/:moduleId/*` — não renderiza nada visível. Só sincroniza a
 * URL com o store de abas (abre/reativa a aba correspondente). O conteúdo de
 * verdade vem do `ModuleWorkspace`, montado uma vez em `AppShell` e nunca
 * desmontado por navegação — é isso que preserva o estado do módulo ao
 * trocar de aba.
 */
export function ModuleRouteSync() {
  const { moduleId } = useParams<{ moduleId: string }>()
  const openTab = useModuleTabsStore((s) => s.openTab)

  useEffect(() => {
    if (!moduleId) return
    let cancelled = false
    registryApi
      .getModule(moduleId)
      .then((entry) => { if (!cancelled) openTab(moduleId, entry.name) })
      .catch(() => { if (!cancelled) openTab(moduleId, moduleId) })
    return () => { cancelled = true }
  }, [moduleId, openTab])

  return null
}
