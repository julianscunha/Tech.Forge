import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
  onPageSizeChange: (pageSize: number) => void
}

export function CatalogPagination({
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
}: Props) {
  const totalPages = Math.ceil(total / pageSize)
  const startItem = (page - 1) * pageSize + 1
  const endItem = Math.min(page * pageSize, total)

  const generatePageNumbers = () => {
    const pages = []
    const showEllipsisBefore = page > 3
    const showEllipsisAfter = page < totalPages - 2

    if (showEllipsisBefore) {
      pages.push(1)
      pages.push('...' as const)
    }

    const rangeStart = Math.max(1, page - 1)
    const rangeEnd = Math.min(totalPages, page + 1)

    for (let i = rangeStart; i <= rangeEnd; i++) {
      pages.push(i)
    }

    if (showEllipsisAfter) {
      pages.push('...' as const)
      pages.push(totalPages)
    }

    if (!showEllipsisBefore && !showEllipsisAfter) {
      // Mostrar todas as páginas se houver poucas
      if (pages.length === 0) {
        for (let i = 1; i <= totalPages; i++) {
          pages.push(i)
        }
      }
    }

    return pages
  }

  const pageNumbers = generatePageNumbers()

  return (
    <div className="px-6 py-4 border-t border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-subtle))]">
      <div className="flex items-center justify-between flex-wrap gap-4">
        {/* Info */}
        <div className="text-xs text-[hsl(var(--text-muted))]">
          Mostrando <span className="font-medium text-[hsl(var(--text))]">{startItem}</span>–<span className="font-medium text-[hsl(var(--text))]">{endItem}</span> de <span className="font-medium text-[hsl(var(--text))]">{total}</span>
        </div>

        {/* Page size selector */}
        <div className="flex items-center gap-2">
          <label htmlFor="page-size" className="text-xs text-[hsl(var(--text-muted))] font-medium">
            Itens por página:
          </label>
          <select
            id="page-size"
            value={pageSize}
            onChange={e => onPageSizeChange(Number(e.target.value))}
            className={cn(
              'px-2 py-1 rounded text-xs border border-[hsl(var(--border-subtle))]',
              'bg-[hsl(var(--bg-elevated))] text-[hsl(var(--text))]',
              'focus:outline-none focus:border-[hsl(var(--accent))]',
            )}
          >
            <option value={12}>12</option>
            <option value={24}>24</option>
            <option value={48}>48</option>
          </select>
        </div>

        {/* Navigation */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page === 1}
            className={cn(
              'p-1.5 rounded border border-[hsl(var(--border-subtle))]',
              'transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
              page === 1
                ? 'bg-[hsl(var(--bg-elevated))] text-[hsl(var(--text-muted))]'
                : 'bg-[hsl(var(--bg-elevated))] text-[hsl(var(--text))] hover:bg-[hsl(var(--bg))]',
            )}
          >
            <ChevronLeft size={16} />
          </button>

          <div className="flex items-center gap-1 px-2">
            {pageNumbers.map((p, idx) => (
              <div key={idx}>
                {p === '...' ? (
                  <span className="text-xs text-[hsl(var(--text-muted))]">…</span>
                ) : (
                  <button
                    onClick={() => onPageChange(p as number)}
                    className={cn(
                      'px-2 py-1 rounded text-xs font-medium transition-colors',
                      p === page
                        ? 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))]'
                        : 'bg-[hsl(var(--bg-elevated))] text-[hsl(var(--text-muted))] hover:bg-[hsl(var(--bg))]',
                    )}
                  >
                    {p}
                  </button>
                )}
              </div>
            ))}
          </div>

          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page === totalPages}
            className={cn(
              'p-1.5 rounded border border-[hsl(var(--border-subtle))]',
              'transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
              page === totalPages
                ? 'bg-[hsl(var(--bg-elevated))] text-[hsl(var(--text-muted))]'
                : 'bg-[hsl(var(--bg-elevated))] text-[hsl(var(--text))] hover:bg-[hsl(var(--bg))]',
            )}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}
