import { useState } from 'react'
import { Terminal, ChevronDown, ChevronRight, Info, AlertTriangle, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { LoaderResult, LoadEvent } from '@/types'

const LEVEL_CONFIG = {
  info:    { icon: Info,          color: 'text-[hsl(var(--text-muted))]',  bg: '' },
  warning: { icon: AlertTriangle, color: 'text-[hsl(var(--warning))]',     bg: 'bg-[hsl(var(--warning)/0.06)]' },
  error:   { icon: AlertCircle,   color: 'text-[hsl(var(--danger))]',      bg: 'bg-[hsl(var(--danger)/0.06)]' },
}

function EventRow({ event }: { event: LoadEvent }) {
  const [open, setOpen] = useState(false)
  const cfg = LEVEL_CONFIG[event.level] ?? LEVEL_CONFIG.info
  const Icon = cfg.icon
  const hasDetails = Object.keys(event.details).length > 0

  const ts = new Date(event.timestamp).toISOString().split('T')[1].slice(0, 12)

  return (
    <div className={cn('rounded px-2.5 py-1.5 font-mono text-[11px]', cfg.bg)}>
      <div
        className={cn('flex items-start gap-2 cursor-default', hasDetails && 'cursor-pointer')}
        onClick={() => hasDetails && setOpen((o) => !o)}
      >
        <span className="text-[hsl(var(--text-subtle))] flex-shrink-0 mt-px">{ts}</span>
        <Icon size={11} className={cn('flex-shrink-0 mt-px', cfg.color)} />
        {event.module_id && (
          <span className="text-[hsl(var(--accent))] flex-shrink-0">[{event.module_id}]</span>
        )}
        <span className={cn('flex-1', cfg.color)}>{event.message}</span>
        {hasDetails && (
          open
            ? <ChevronDown size={11} className="flex-shrink-0 text-[hsl(var(--text-subtle))]" />
            : <ChevronRight size={11} className="flex-shrink-0 text-[hsl(var(--text-subtle))]" />
        )}
      </div>
      {open && hasDetails && (
        <pre className="mt-1 ml-[64px] text-[10px] text-[hsl(var(--text-muted))] whitespace-pre-wrap">
          {JSON.stringify(event.details, null, 2)}
        </pre>
      )}
    </div>
  )
}

interface Props {
  result: LoaderResult
}

export function LoaderJournalViewer({ result }: Props) {
  const [filter, setFilter] = useState<'all' | 'info' | 'warning' | 'error'>('all')

  const filtered = filter === 'all'
    ? result.journal
    : result.journal.filter((e) => e.level === filter)

  return (
    <div className="rounded-lg border border-[hsl(var(--border-subtle))] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[hsl(var(--bg-elevated))] border-b border-[hsl(var(--border-subtle))]">
        <div className="flex items-center gap-2">
          <Terminal size={13} className="text-[hsl(var(--accent))]" />
          <span className="text-xs font-medium text-[hsl(var(--text))]">Loader Journal</span>
          <span className="text-xs font-mono text-[hsl(var(--text-subtle))]">
            ({result.journal.length} events)
          </span>
        </div>

        {/* Filter pills */}
        <div className="flex items-center gap-1">
          {(['all', 'info', 'warning', 'error'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                'px-2 py-0.5 rounded text-[10px] font-medium transition-colors capitalize',
                filter === f
                  ? 'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))]'
                  : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]'
              )}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Summary strip */}
      <div className="flex items-center gap-4 px-4 py-2 bg-[hsl(var(--bg))] border-b border-[hsl(var(--border-subtle))] text-[10px]">
        <Pill label="Scanned"     value={result.scanned}      color="text-[hsl(var(--text-muted))]" />
        <Pill label="Installed"   value={result.installed}    color="text-[hsl(var(--success))]" />
        <Pill label="Disabled"    value={result.disabled}     color="text-[hsl(var(--text-subtle))]" />
        <Pill label="Invalid"     value={result.invalid}      color="text-[hsl(var(--danger))]" />
        <Pill label="Incompatible" value={result.incompatible} color="text-[hsl(var(--warning))]" />
      </div>

      {/* Log lines */}
      <div className="max-h-72 overflow-y-auto bg-[hsl(var(--bg))] p-2 space-y-0.5">
        {filtered.length === 0 ? (
          <p className="text-center py-6 text-[11px] text-[hsl(var(--text-subtle))] font-mono">
            No {filter} events.
          </p>
        ) : (
          filtered.map((event, i) => <EventRow key={i} event={event} />)
        )}
      </div>
    </div>
  )
}

function Pill({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <span className="flex items-center gap-1 font-mono">
      <span className="text-[hsl(var(--text-subtle))]">{label}:</span>
      <span className={cn('font-semibold', color)}>{value}</span>
    </span>
  )
}
