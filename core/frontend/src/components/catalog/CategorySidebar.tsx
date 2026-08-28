import { useEffect, useState } from 'react'
import { catalogApi } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { CatalogCategory } from '@/types'

interface Props {
  selected: string | null
  onSelect: (category: string | null) => void
  loading?: boolean
}

export function CategorySidebar({ selected, onSelect, loading = false }: Props) {
  const [categories, setCategories] = useState<CatalogCategory[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetch = async () => {
      try {
        const cats = await catalogApi.categories()
        setCategories(cats)
        setError(null)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Erro ao carregar categorias')
      }
    }
    fetch()
  }, [])

  const totalCount = categories.reduce((sum, c) => sum + c.count, 0)

  return (
    <div className="w-56 flex-shrink-0 border-r border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-subtle))] overflow-y-auto">
      <div className="p-4 space-y-1">
        {/* Todas */}
        <button
          onClick={() => onSelect(null)}
          disabled={loading}
          className={cn(
            'w-full text-left px-3 py-2 rounded text-sm transition-colors disabled:opacity-50',
            selected === null
              ? 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))] font-medium'
              : 'text-[hsl(var(--text-muted))] hover:bg-[hsl(var(--bg-elevated))]',
          )}
        >
          <span className="flex items-center justify-between">
            <span>Todas</span>
            <span className={cn(
              'text-xs font-medium px-2 py-0.5 rounded-full',
              selected === null
                ? 'bg-[hsl(var(--accent)/0.2)] text-[hsl(var(--accent))]'
                : 'bg-[hsl(var(--bg-elevated))] text-[hsl(var(--text-subtle))]',
            )}>
              {totalCount}
            </span>
          </span>
        </button>

        {/* Categorias */}
        {error ? (
          <p className="text-xs text-[hsl(var(--danger))] px-3 py-2">{error}</p>
        ) : categories.length === 0 ? (
          <p className="text-xs text-[hsl(var(--text-muted))] px-3 py-2">Nenhuma categoria</p>
        ) : (
          categories.map(cat => (
            <button
              key={cat.name}
              onClick={() => onSelect(cat.name)}
              disabled={loading}
              className={cn(
                'w-full text-left px-3 py-2 rounded text-sm transition-colors disabled:opacity-50',
                selected === cat.name
                  ? 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))] font-medium'
                  : 'text-[hsl(var(--text-muted))] hover:bg-[hsl(var(--bg-elevated))]',
              )}
            >
              <span className="flex items-center justify-between">
                <span>{cat.name}</span>
                <span className={cn(
                  'text-xs font-medium px-2 py-0.5 rounded-full',
                  selected === cat.name
                    ? 'bg-[hsl(var(--accent)/0.2)] text-[hsl(var(--accent))]'
                    : 'bg-[hsl(var(--bg-elevated))] text-[hsl(var(--text-subtle))]',
                )}>
                  {cat.count}
                </span>
              </span>
            </button>
          ))
        )}
      </div>
    </div>
  )
}
