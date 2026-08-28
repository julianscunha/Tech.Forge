import { useState, useEffect, useRef } from 'react'
import { Search, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { CatalogSourceType, TrustLevel } from '@/types'
import type { CatalogListParams } from '@/lib/api'

interface Props {
  onChange: (params: Partial<CatalogListParams>) => void
}

const SOURCES: { value: CatalogSourceType; label: string }[] = [
  { value: 'local', label: 'Local' },
  { value: 'official_catalog', label: 'Oficial' },
  { value: 'custom_catalog', label: 'Custom' },
]

const TRUST_LEVELS: { value: TrustLevel; label: string }[] = [
  { value: 'TRUSTED', label: 'Confiável' },
  { value: 'VERIFIED', label: 'Verificado' },
  { value: 'UNVERIFIED', label: 'Não verificado' },
  { value: 'MODIFIED', label: 'Modificado' },
  { value: 'INVALID', label: 'Inválido' },
]

const SORT_OPTIONS: { value: 'name' | 'recent'; label: string }[] = [
  { value: 'name', label: 'Nome' },
  { value: 'recent', label: 'Recente' },
]

export function CatalogFilterBar({ onChange }: Props) {
  const [search, setSearch] = useState('')
  const [selectedSources, setSelectedSources] = useState<CatalogSourceType[]>([])
  const [selectedTrustLevels, setSelectedTrustLevels] = useState<TrustLevel[]>([])
  const [compatibleOnly, setCompatibleOnly] = useState(false)
  const [installedOnly, setInstalledOnly] = useState(false)
  const [favoritesOnly, setFavoritesOnly] = useState(false)
  const [sort, setSort] = useState<'name' | 'recent'>('name')
  const searchTimeout = useRef<NodeJS.Timeout | null>(null)

  // Debounce search
  useEffect(() => {
    if (searchTimeout.current) clearTimeout(searchTimeout.current)
    searchTimeout.current = setTimeout(() => {
      onChange({ search: search || undefined })
    }, 300)
    return () => {
      if (searchTimeout.current) clearTimeout(searchTimeout.current)
    }
  }, [search, onChange])

  const handleSourceToggle = (source: CatalogSourceType) => {
    const newSources = selectedSources.includes(source)
      ? selectedSources.filter(s => s !== source)
      : [...selectedSources, source]
    setSelectedSources(newSources)
    onChange({ source: newSources.length > 0 ? newSources.join(',') : undefined })
  }

  const handleTrustToggle = (level: TrustLevel) => {
    const newLevels = selectedTrustLevels.includes(level)
      ? selectedTrustLevels.filter(l => l !== level)
      : [...selectedTrustLevels, level]
    setSelectedTrustLevels(newLevels)
    onChange({ trust_level: newLevels.length > 0 ? newLevels.join(',') : undefined })
  }

  const handleCompatibleToggle = (value: boolean) => {
    setCompatibleOnly(value)
    onChange({ compatible_only: value })
  }

  const handleInstalledToggle = (value: boolean) => {
    setInstalledOnly(value)
    onChange({ installed_only: value })
  }

  const handleFavoritesToggle = (value: boolean) => {
    setFavoritesOnly(value)
    onChange({ favorites_only: value })
  }

  const handleSortChange = (newSort: 'name' | 'recent') => {
    setSort(newSort)
    onChange({ sort: newSort })
  }

  return (
    <div className="space-y-3 p-4 border-b border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-subtle))]">
      {/* Search */}
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))]" />
        <input
          type="text"
          placeholder="Buscar módulos..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className={cn(
            'w-full pl-9 pr-3 py-2 rounded border border-[hsl(var(--border-subtle))]',
            'bg-[hsl(var(--bg-elevated))] text-[hsl(var(--text))]',
            'placeholder:text-[hsl(var(--text-muted))]',
            'focus:outline-none focus:border-[hsl(var(--accent))]',
          )}
        />
        {search && (
          <button
            onClick={() => setSearch('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Filter chips */}
      <div className="space-y-2">
        {/* Fonte */}
        <div>
          <p className="text-xs font-medium text-[hsl(var(--text-muted))] mb-1.5">Fonte</p>
          <div className="flex flex-wrap gap-1.5">
            {SOURCES.map(source => (
              <button
                key={source.value}
                onClick={() => handleSourceToggle(source.value)}
                className={cn(
                  'px-2.5 py-1 rounded text-xs font-medium transition-colors',
                  selectedSources.includes(source.value)
                    ? 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))]'
                    : 'bg-[hsl(var(--bg-elevated))] text-[hsl(var(--text-muted))] hover:bg-[hsl(var(--border-subtle))]',
                )}
              >
                {source.label}
              </button>
            ))}
          </div>
        </div>

        {/* Trust Level */}
        <div>
          <p className="text-xs font-medium text-[hsl(var(--text-muted))] mb-1.5">Nível de confiança</p>
          <div className="flex flex-wrap gap-1.5">
            {TRUST_LEVELS.map(level => (
              <button
                key={level.value}
                onClick={() => handleTrustToggle(level.value)}
                className={cn(
                  'px-2.5 py-1 rounded text-xs font-medium transition-colors',
                  selectedTrustLevels.includes(level.value)
                    ? 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))]'
                    : 'bg-[hsl(var(--bg-elevated))] text-[hsl(var(--text-muted))] hover:bg-[hsl(var(--border-subtle))]',
                )}
              >
                {level.label}
              </button>
            ))}
          </div>
        </div>

        {/* Toggles */}
        <div className="flex flex-wrap gap-3">
          <label className="flex items-center gap-2 text-xs cursor-pointer">
            <input
              type="checkbox"
              checked={compatibleOnly}
              onChange={e => handleCompatibleToggle(e.target.checked)}
              className="rounded"
            />
            <span className="text-[hsl(var(--text-muted))]">Somente compatíveis</span>
          </label>
          <label className="flex items-center gap-2 text-xs cursor-pointer">
            <input
              type="checkbox"
              checked={installedOnly}
              onChange={e => handleInstalledToggle(e.target.checked)}
              className="rounded"
            />
            <span className="text-[hsl(var(--text-muted))]">Somente instalados</span>
          </label>
          <label className="flex items-center gap-2 text-xs cursor-pointer">
            <input
              type="checkbox"
              checked={favoritesOnly}
              onChange={e => handleFavoritesToggle(e.target.checked)}
              className="rounded"
            />
            <span className="text-[hsl(var(--text-muted))]">Somente favoritos</span>
          </label>
        </div>

        {/* Sort */}
        <div className="flex items-center gap-2">
          <p className="text-xs font-medium text-[hsl(var(--text-muted))]">Ordenar por:</p>
          <select
            value={sort}
            onChange={e => handleSortChange(e.target.value as 'name' | 'recent')}
            className={cn(
              'px-2 py-1 rounded text-xs border border-[hsl(var(--border-subtle))]',
              'bg-[hsl(var(--bg-elevated))] text-[hsl(var(--text))]',
              'focus:outline-none focus:border-[hsl(var(--accent))]',
            )}
          >
            {SORT_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  )
}
