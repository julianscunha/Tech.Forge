import { useEffect, useState } from 'react'
import { X, Plus, Check, AlertCircle, RefreshCw } from 'lucide-react'
import { catalogApi } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { CatalogSourceConfig } from '@/types'

interface Props {
  onClose: () => void
  onRefresh?: () => void
}

export function CatalogSourcesPanel({ onClose, onRefresh }: Props) {
  const [sources, setSources] = useState<CatalogSourceConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newSourceName, setNewSourceName] = useState('')
  const [newSourceUrl, setNewSourceUrl] = useState('')
  const [adding, setAdding] = useState(false)
  const [addError, setAddError] = useState<string | null>(null)

  useEffect(() => {
    const fetch = async () => {
      try {
        const srcs = await catalogApi.sources()
        setSources(srcs)
        setError(null)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Erro ao carregar fontes')
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [])

  const handleAddSource = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newSourceName.trim() || !newSourceUrl.trim()) return

    setAdding(true)
    setAddError(null)
    try {
      const newSource = await catalogApi.addSource({
        name: newSourceName,
        url: newSourceUrl,
        type: 'custom_catalog',
      })
      setSources(prev => [...prev, newSource])
      setNewSourceName('')
      setNewSourceUrl('')
      onRefresh?.()
    } catch (e) {
      setAddError(e instanceof Error ? e.message : 'Erro ao adicionar fonte')
    } finally {
      setAdding(false)
    }
  }

  const handleRemoveSource = async (sourceId: string) => {
    if (!window.confirm('Remover esta fonte?')) return
    try {
      await catalogApi.removeSource(sourceId)
      setSources(prev => prev.filter(s => s.id !== sourceId))
      onRefresh?.()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao remover fonte')
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
      <div className={cn(
        'w-full max-w-md rounded-lg border border-[hsl(var(--border-subtle))]',
        'bg-[hsl(var(--bg-elevated))] shadow-lg',
        'flex flex-col max-h-[80vh] overflow-hidden',
      )}>
        {/* Header */}
        <div className="px-6 py-4 border-b border-[hsl(var(--border-subtle))] flex items-center justify-between flex-shrink-0">
          <h2 className="text-base font-semibold text-[hsl(var(--text))]">
            Gerenciar fontes
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-[hsl(var(--bg-subtle))] text-[hsl(var(--text-muted))]"
          >
            <X size={16} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {/* Error */}
          {error && (
            <div className="flex items-start gap-2 p-3 rounded-lg bg-[hsl(var(--danger)/0.1)] border border-[hsl(var(--danger)/0.2)]">
              <AlertCircle size={14} className="text-[hsl(var(--danger))] flex-shrink-0 mt-0.5" />
              <p className="text-xs text-[hsl(var(--danger))]">{error}</p>
            </div>
          )}

          {/* Sources list */}
          {loading ? (
            <div className="text-center py-6">
              <RefreshCw size={16} className="mx-auto mb-2 text-[hsl(var(--text-muted))] animate-spin" />
              <p className="text-xs text-[hsl(var(--text-muted))]">Carregando fontes...</p>
            </div>
          ) : sources.length === 0 ? (
            <p className="text-xs text-[hsl(var(--text-muted))] text-center py-4">Nenhuma fonte customizada</p>
          ) : (
            <div className="space-y-2">
              {sources.map(source => (
                <div
                  key={source.id}
                  className="flex items-start gap-3 p-3 rounded-lg border border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg))]"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[hsl(var(--text))] truncate">{source.name}</p>
                    <p className="text-xs text-[hsl(var(--text-muted))] truncate mt-0.5">{source.url}</p>
                    <div className="flex items-center gap-1.5 mt-1.5">
                      {source.status === 'available' ? (
                        <>
                          <Check size={12} className="text-[hsl(var(--success))]" />
                          <span className="text-[10px] text-[hsl(var(--success))] font-medium">Disponível</span>
                        </>
                      ) : (
                        <>
                          <AlertCircle size={12} className="text-[hsl(var(--warning))]" />
                          <span className="text-[10px] text-[hsl(var(--warning))] font-medium">Indisponível</span>
                        </>
                      )}
                    </div>
                  </div>
                  {source.type === 'custom_catalog' && (
                    <button
                      onClick={() => handleRemoveSource(source.id)}
                      className="p-1.5 rounded hover:bg-[hsl(var(--danger)/0.1)] text-[hsl(var(--danger))] flex-shrink-0"
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Add source form */}
          <div className="pt-4 border-t border-[hsl(var(--border-subtle))]">
            <h3 className="text-xs font-medium text-[hsl(var(--text-muted))] mb-3 flex items-center gap-2">
              <Plus size={12} /> Adicionar fonte customizada
            </h3>
            <form onSubmit={handleAddSource} className="space-y-2">
              <div>
                <label htmlFor="src-name" className="text-xs font-medium text-[hsl(var(--text-muted))] block mb-1">
                  Nome
                </label>
                <input
                  id="src-name"
                  type="text"
                  value={newSourceName}
                  onChange={e => setNewSourceName(e.target.value)}
                  placeholder="Ex: Meus Módulos"
                  className={cn(
                    'w-full px-2 py-1.5 rounded text-xs border border-[hsl(var(--border-subtle))]',
                    'bg-[hsl(var(--bg))] text-[hsl(var(--text))]',
                    'placeholder:text-[hsl(var(--text-muted))]',
                    'focus:outline-none focus:border-[hsl(var(--accent))]',
                  )}
                />
              </div>
              <div>
                <label htmlFor="src-url" className="text-xs font-medium text-[hsl(var(--text-muted))] block mb-1">
                  URL do repositório
                </label>
                <input
                  id="src-url"
                  type="text"
                  value={newSourceUrl}
                  onChange={e => setNewSourceUrl(e.target.value)}
                  placeholder="Ex: https://github.com/user/modules"
                  className={cn(
                    'w-full px-2 py-1.5 rounded text-xs border border-[hsl(var(--border-subtle))]',
                    'bg-[hsl(var(--bg))] text-[hsl(var(--text))]',
                    'placeholder:text-[hsl(var(--text-muted))]',
                    'focus:outline-none focus:border-[hsl(var(--accent))]',
                  )}
                />
                <p className="text-[10px] text-[hsl(var(--text-muted))] mt-1">
                  Use GitHub, GitLab ou similar com estrutura: <code className="bg-[hsl(var(--bg-subtle))] px-1 rounded">modules/&lt;id&gt;/manifest.yaml</code>
                </p>
              </div>
              {addError && (
                <div className="flex items-start gap-2 p-2 rounded bg-[hsl(var(--danger)/0.1)]">
                  <AlertCircle size={12} className="text-[hsl(var(--danger))] flex-shrink-0 mt-0.5" />
                  <p className="text-[10px] text-[hsl(var(--danger))]">{addError}</p>
                </div>
              )}
              <button
                type="submit"
                disabled={adding || !newSourceName.trim() || !newSourceUrl.trim()}
                className={cn(
                  'w-full px-3 py-2 rounded text-xs font-medium',
                  'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))]',
                  'hover:bg-[hsl(var(--accent)/0.2)] transition-colors',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                )}
              >
                {adding ? 'Adicionando...' : 'Adicionar'}
              </button>
            </form>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[hsl(var(--border-subtle))] flex-shrink-0">
          <button
            onClick={onClose}
            className={cn(
              'w-full px-4 py-2 rounded text-sm font-medium',
              'bg-[hsl(var(--bg-subtle))] text-[hsl(var(--text-muted))]',
              'hover:bg-[hsl(var(--bg))] transition-colors',
            )}
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  )
}
