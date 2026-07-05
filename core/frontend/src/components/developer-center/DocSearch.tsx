import { useState, useEffect, useRef } from 'react'
import { Search, X, FileText } from 'lucide-react'
import { docsApi } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { DocSearchResult } from '@/types'

const CATEGORY_LABELS: Record<string, string> = {
  intro:          'Introdução',
  architecture:   'Arquitetura',
  guide:          'Guia',
  'sdk-backend':  'SDK Backend',
  'sdk-frontend': 'SDK Frontend',
  'service-module': 'Service Module',
  examples:       'Exemplos',
  'manifest-reference': 'Manifest',
  marketplace:    'Marketplace',
  faq:            'FAQ',
  module:         'Módulo',
}

interface Props {
  onSelect: (docId: string) => void
}

export function DocSearch({ onSelect }: Props) {
  const [query,   setQuery]   = useState('')
  const [results, setResults] = useState<DocSearchResult[]>([])
  const [open,    setOpen]    = useState(false)
  const [loading, setLoading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!query.trim()) { setResults([]); setOpen(false); return }

    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const r = await docsApi.search(query, 8)
        setResults(r)
        setOpen(true)
      } catch { setResults([]) }
      finally { setLoading(false) }
    }, 250)

    return () => { if (timerRef.current) clearTimeout(timerRef.current) }
  }, [query])

  const handleSelect = (docId: string) => {
    onSelect(docId)
    setQuery('')
    setOpen(false)
    inputRef.current?.blur()
  }

  return (
    <div className="relative w-full max-w-sm">
      {/* Input */}
      <div className="relative">
        <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-subtle))]" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
          placeholder="Buscar documentação…"
          className={cn(
            'w-full pl-7 pr-7 py-1.5 rounded text-xs',
            'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border-subtle))]',
            'text-[hsl(var(--text))] placeholder:text-[hsl(var(--text-subtle))]',
            'focus:outline-none focus:border-[hsl(var(--accent)/0.5)] transition-colors',
          )}
        />
        {query && (
          <button
            onClick={() => { setQuery(''); setOpen(false) }}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-[hsl(var(--text-subtle))] hover:text-[hsl(var(--text))]"
          >
            <X size={11} />
          </button>
        )}
      </div>

      {/* Results dropdown */}
      {open && results.length > 0 && (
        <div className={cn(
          'absolute top-full mt-1 left-0 right-0 z-50',
          'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border))]',
          'rounded-lg shadow-xl overflow-hidden',
        )}>
          {results.map(r => (
            <button
              key={r.doc_id}
              onClick={() => handleSelect(r.doc_id)}
              className={cn(
                'w-full text-left px-3 py-2.5 flex items-start gap-2.5',
                'hover:bg-[hsl(var(--bg-subtle))] transition-colors border-b border-[hsl(var(--border-subtle))] last:border-0',
              )}
            >
              <FileText size={13} className="text-[hsl(var(--accent))] flex-shrink-0 mt-0.5" />
              <div className="min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-xs font-medium text-[hsl(var(--text))] truncate">{r.title}</span>
                  <span className="text-[10px] text-[hsl(var(--text-subtle))] flex-shrink-0">
                    {CATEGORY_LABELS[r.category] ?? r.category}
                  </span>
                </div>
                <p className="text-[11px] text-[hsl(var(--text-muted))] truncate">{r.excerpt}</p>
              </div>
            </button>
          ))}
        </div>
      )}

      {open && loading && (
        <div className="absolute top-full mt-1 left-0 right-0 bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border))] rounded-lg px-3 py-2.5 text-xs text-[hsl(var(--text-muted))] z-50">
          Buscando…
        </div>
      )}
    </div>
  )
}
