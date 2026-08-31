import { useEffect, useState, useCallback } from 'react'
import {
  BookOpen, Code2, Layers, Puzzle, FileText, HelpCircle,
  Package, Zap, ChevronRight, Download, RefreshCw,
  Store, LayoutGrid, ShieldCheck, GitBranch, Boxes,
} from 'lucide-react'
import { docsApi, servicesApi, dependenciesApi } from '@/lib/api'
import { MarkdownRenderer } from '@/components/developer-center/MarkdownRenderer'
import { DocSearch } from '@/components/developer-center/DocSearch'
import { ServiceContractPanel } from '@/components/developer-center/ServiceContractPanel'
import { MermaidDiagram } from '@/components/developer-center/MermaidDiagram'
import { cn } from '@/lib/utils'
import type { DocEntryMeta, DocEntryFull, ServiceContract, ServiceStatus } from '@/types'

// ── Sidebar config ────────────────────────────────────────────────────────────

interface SidebarSection {
  id:       string
  label:    string
  icon:     typeof BookOpen
  category: string
}

const SIDEBAR_SECTIONS: SidebarSection[] = [
  { id: 'intro',          label: 'Introdução',              icon: BookOpen,  category: 'intro'          },
  { id: 'architecture',   label: 'Arquitetura TechForge',   icon: Layers,    category: 'architecture'   },
  { id: 'guide',          label: 'Guia de Desenvolvimento', icon: Code2,     category: 'guide'          },
  { id: 'modules',        label: 'Módulos Instalados',      icon: Boxes,     category: 'module'         },
  { id: 'sdk-backend',    label: 'SDK Backend',             icon: Zap,       category: 'sdk-backend'    },
  { id: 'sdk-frontend',   label: 'SDK Frontend',            icon: LayoutGrid, category: 'sdk-frontend'  },
  { id: 'service-module', label: 'Service Modules',         icon: Puzzle,    category: 'service-module' },
  { id: 'examples',       label: 'Exemplos',                icon: FileText,  category: 'examples'       },
  { id: 'manifest-reference', label: 'Referência do Manifesto', icon: Package, category: 'manifest-reference' },
  { id: 'marketplace',    label: 'Marketplace para Devs',   icon: Store,     category: 'marketplace'    },
  { id: 'governance',     label: 'Documentation First',      icon: ShieldCheck, category: 'governance'  },
  { id: 'dependency-graph', label: 'Dependency Graph',       icon: GitBranch, category: 'dependency-graph' },
  { id: 'faq',            label: 'FAQ',                     icon: HelpCircle, category: 'faq'           },
]

// ── Main page ─────────────────────────────────────────────────────────────────

export function DeveloperCenterPage() {
  const [activeSection,   setActiveSection]   = useState('intro')
  const [articles,        setArticles]        = useState<DocEntryMeta[]>([])
  const [selectedArticle, setSelectedArticle] = useState<DocEntryFull | null>(null)
  const [contracts,       setContracts]       = useState<ServiceContract[]>([])
  const [serviceStatus,   setServiceStatus]   = useState<Record<string, ServiceStatus>>({})
  const [mermaidGraph,    setMermaidGraph]    = useState<string | null>(null)
  const [loading,         setLoading]         = useState(false)
  const [exporting,       setExporting]       = useState(false)
  const [reindexing,      setReindexing]      = useState(false)
  const [exportMsg,       setExportMsg]       = useState<string | null>(null)

  const loadSection = useCallback(async (sectionId: string) => {
    const section = SIDEBAR_SECTIONS.find(s => s.id === sectionId)
    if (!section) return
    setLoading(true)
    // NÃO reseta selectedArticle aqui — isso roda toda vez que activeSection
    // muda, inclusive quando é a busca navegando pra seção certa de um
    // artigo que acabou de abrir (handleSearch muda activeSection E abre o
    // artigo quase ao mesmo tempo; resetar aqui apagava o artigo numa
    // corrida entre os dois fetches). Quem troca de seção de propósito
    // (clique na sidebar) já reseta explicitamente no próprio onClick.
    setMermaidGraph(null)
    try {
      if (sectionId === 'dependency-graph') {
        const { mermaid } = await dependenciesApi.graph()
        setMermaidGraph(mermaid)
        setArticles([])
        setContracts([])
        setServiceStatus({})
      } else if (sectionId === 'modules') {
        // README/overview.md de cada módulo instalado + os exemplos por
        // módulo (categorias distintas no indexador, mesma seção na UI).
        const [overviews, examples] = await Promise.all([
          docsApi.list('module'),
          docsApi.list('module-example'),
        ])
        setArticles([...overviews, ...examples])
        setContracts([])
        setServiceStatus({})
      } else if (sectionId === 'service-module') {
        const [arts, conts, services] = await Promise.all([
          docsApi.list(section.category),
          docsApi.contracts(),
          servicesApi.list().catch(() => []),
        ])
        setArticles(arts)
        setContracts(conts)
        setServiceStatus(Object.fromEntries(services.map(s => [s.service_id, s.status])))
      } else {
        const arts = await docsApi.list(section.category)
        setArticles(arts)
        setContracts([])
        setServiceStatus({})
      }
    } catch { setArticles([]); setContracts([]); setServiceStatus({}) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { loadSection(activeSection) }, [activeSection, loadSection])

  const openArticle = async (docId: string) => {
    setLoading(true)
    try {
      const art = await docsApi.article(docId)
      setSelectedArticle(art)
    } catch { setSelectedArticle(null) }
    finally { setLoading(false) }
  }

  const handleSearch = (docId: string, category: string) => {
    openArticle(docId)
    // Resolve pela categoria do próprio resultado da busca, não pela lista
    // de artigos já carregada na seção atual — o resultado quase sempre é
    // de OUTRA seção (por isso o usuário estava buscando). "module-example"
    // não tem seção própria na sidebar, cai na mesma seção de "module".
    const resolvedCategory = category === 'module-example' ? 'module' : category
    const section = SIDEBAR_SECTIONS.find(s => s.category === resolvedCategory)
    if (section) setActiveSection(section.id)
  }

  const handleExportAI = async () => {
    setExporting(true)
    setExportMsg(null)
    try {
      const md = await docsApi.exportAI()
      const blob = new Blob([md], { type: 'text/markdown' })
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = 'techforge-ai-context.md'
      a.click()
      URL.revokeObjectURL(url)
      setExportMsg('Exportado com sucesso.')
    } catch { setExportMsg('Erro ao exportar.') }
    finally { setExporting(false); setTimeout(() => setExportMsg(null), 3000) }
  }

  const handleReindex = async () => {
    setReindexing(true)
    try {
      const r = await docsApi.reindex()
      await loadSection(activeSection)
      setExportMsg(`${r.indexed} documentos reindexados.`)
      setTimeout(() => setExportMsg(null), 3000)
    } catch { setExportMsg('Erro ao reindexar.') } finally { setReindexing(false) }
  }

  const activeConfig = SIDEBAR_SECTIONS.find(s => s.id === activeSection)

  return (
    <div className="flex h-full overflow-hidden">

      {/* ── Left sidebar ────────────────────────────────────────────────── */}
      <aside className="w-56 flex-shrink-0 flex flex-col border-r border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-elevated))] overflow-hidden">
        {/* Header */}
        <div className="px-4 py-3 border-b border-[hsl(var(--border-subtle))]">
          <div className="flex items-center gap-2 mb-2">
            <BookOpen size={14} className="text-[hsl(var(--accent))]" />
            <span className="text-xs font-semibold text-[hsl(var(--text))]">Developer Center</span>
          </div>
          <DocSearch onSelect={handleSearch} />
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
          {SIDEBAR_SECTIONS.map(sec => {
            const Icon = sec.icon
            const isActive = activeSection === sec.id
            return (
              <button
                key={sec.id}
                onClick={() => { setActiveSection(sec.id); setSelectedArticle(null) }}
                className={cn(
                  'w-full flex items-center gap-2 px-2 py-1.5 rounded text-xs text-left transition-colors',
                  isActive
                    ? 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))] font-medium'
                    : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] hover:bg-[hsl(var(--bg-subtle))]',
                )}
              >
                <Icon size={13} className="flex-shrink-0" />
                <span className="truncate">{sec.label}</span>
              </button>
            )
          })}
        </nav>

        {/* Footer actions */}
        <div className="px-2 py-2 border-t border-[hsl(var(--border-subtle))] space-y-1">
          <button
            onClick={handleExportAI}
            disabled={exporting}
            className={cn(
              'w-full flex items-center gap-2 px-2 py-1.5 rounded text-xs transition-colors',
              'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] hover:bg-[hsl(var(--bg-subtle))]',
              'disabled:opacity-50',
            )}
          >
            {exporting ? <RefreshCw size={12} className="animate-spin" /> : <Download size={12} />}
            Export AI Context
          </button>
          <button
            onClick={handleReindex}
            disabled={reindexing}
            className={cn(
              'w-full flex items-center gap-2 px-2 py-1.5 rounded text-xs transition-colors',
              'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] hover:bg-[hsl(var(--bg-subtle))]',
              'disabled:opacity-50',
            )}
          >
            <RefreshCw size={12} className={reindexing ? 'animate-spin' : ''} />
            Reindexar
          </button>
          {exportMsg && (
            <p className="text-[10px] text-[hsl(var(--success))] px-2">{exportMsg}</p>
          )}
        </div>
      </aside>

      {/* ── Main content ────────────────────────────────────────────────── */}
      <div className="flex-1 flex overflow-hidden min-w-0">

        {/* Article list (only when no article selected, not for dependency-graph) */}
        {!selectedArticle && activeSection !== 'dependency-graph' && (
          <div className="w-64 flex-shrink-0 border-r border-[hsl(var(--border-subtle))] overflow-y-auto bg-[hsl(var(--bg))]">
            <div className="px-4 py-3 border-b border-[hsl(var(--border-subtle))]">
              <h2 className="text-xs font-semibold text-[hsl(var(--text))] flex items-center gap-2">
                {activeConfig && <activeConfig.icon size={13} className="text-[hsl(var(--accent))]" />}
                {activeConfig?.label}
              </h2>
            </div>
            <div className="py-1">
              {loading ? (
                <div className="px-4 py-8 text-xs text-[hsl(var(--text-subtle))] text-center">
                  Carregando…
                </div>
              ) : articles.length === 0 ? (
                <div className="px-4 py-8 text-xs text-[hsl(var(--text-subtle))] text-center">
                  Nenhum documento nesta seção.
                </div>
              ) : (
                articles.map(art => (
                  <button
                    key={art.id}
                    onClick={() => openArticle(art.id)}
                    className="w-full text-left px-4 py-2.5 hover:bg-[hsl(var(--bg-subtle))] transition-colors
                      border-b border-[hsl(var(--border-subtle))] last:border-0"
                  >
                    <p className="text-xs font-medium text-[hsl(var(--text))] truncate mb-0.5">
                      {art.title}
                    </p>
                    <p className="text-[11px] text-[hsl(var(--text-muted))] line-clamp-2 leading-relaxed">
                      {art.excerpt}
                    </p>
                    {art.tags.length > 0 && (
                      <div className="flex gap-1 mt-1.5 flex-wrap">
                        {art.tags.slice(0, 3).map(tag => (
                          <span key={tag} className="text-[9px] px-1.5 py-0.5 rounded-full
                            bg-[hsl(var(--bg-subtle))] text-[hsl(var(--text-subtle))]">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </button>
                ))
              )}

              {/* Service contracts section */}
              {contracts.length > 0 && (
                <div className="mt-2">
                  <p className="px-4 py-1.5 text-[10px] uppercase tracking-widest font-medium
                    text-[hsl(var(--text-subtle))] border-t border-b border-[hsl(var(--border-subtle))]
                    bg-[hsl(var(--bg-subtle))]">
                    Contratos de Serviço
                  </p>
                  {contracts.map(c => (
                    <button
                      key={c.service_id}
                      onClick={() => setSelectedArticle({
                        id: `contract:${c.service_id}`,
                        title: c.service_id,
                        category: 'service-module',
                        order: 1,
                        tags: [],
                        excerpt: c.description,
                        module_id: c.module_id,
                        content: '__contract__',
                      })}
                      className="w-full text-left px-4 py-2.5 hover:bg-[hsl(var(--bg-subtle))] transition-colors
                        border-b border-[hsl(var(--border-subtle))] last:border-0"
                    >
                      <p className="text-xs font-medium text-[hsl(var(--accent))] font-mono truncate">
                        {c.service_id}
                      </p>
                      <p className="text-[11px] text-[hsl(var(--text-muted))] truncate">{c.description}</p>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Article reader */}
        <div className="flex-1 overflow-y-auto">
          {activeSection === 'dependency-graph' ? (
            <div className="max-w-4xl mx-auto px-8 py-8">
              <h1 className="text-xl font-semibold text-[hsl(var(--text))] mb-1">Dependency Graph</h1>
              <p className="text-xs text-[hsl(var(--text-muted))] mb-6">
                Topologia real de dependências entre módulos instalados.
              </p>
              {loading ? (
                <p className="text-xs text-[hsl(var(--text-subtle))]">Carregando…</p>
              ) : mermaidGraph && mermaidGraph.split('\n').length > 1 ? (
                <MermaidDiagram chart={mermaidGraph} />
              ) : (
                <p className="text-xs text-[hsl(var(--text-subtle))]">
                  Nenhuma dependência declarada entre os módulos instalados.
                </p>
              )}
            </div>
          ) : selectedArticle ? (
            <div className="max-w-3xl mx-auto px-8 py-8">
              {/* Back button */}
              <button
                onClick={() => setSelectedArticle(null)}
                className="flex items-center gap-1.5 text-xs text-[hsl(var(--text-muted))]
                  hover:text-[hsl(var(--text))] mb-6 transition-colors"
              >
                <ChevronRight size={12} className="rotate-180" />
                {activeConfig?.label}
              </button>

              {/* Service contract view */}
              {selectedArticle.content === '__contract__' ? (
                (() => {
                  const contractId = selectedArticle.id.replace('contract:', '')
                  const contract = contracts.find(c => c.service_id === contractId)
                  return contract ? (
                    <>
                      <h1 className="text-xl font-semibold text-[hsl(var(--text))] mb-1">
                        {selectedArticle.title}
                      </h1>
                      <p className="text-xs text-[hsl(var(--text-muted))] mb-6">
                        Módulo: <code className="font-mono text-[hsl(var(--accent))]">{selectedArticle.module_id}</code>
                      </p>
                      <ServiceContractPanel contract={contract} status={serviceStatus[contract.service_id]} />
                    </>
                  ) : null
                })()
              ) : (
                /* Markdown article view */
                <MarkdownRenderer content={selectedArticle.content} />
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center px-8">
              <BookOpen size={32} className="text-[hsl(var(--text-subtle))] mb-3" />
              <p className="text-sm font-medium text-[hsl(var(--text))] mb-1">
                Selecione um artigo
              </p>
              <p className="text-xs text-[hsl(var(--text-muted))] max-w-xs">
                Escolha uma seção e um artigo na lista à esquerda para começar a leitura.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
