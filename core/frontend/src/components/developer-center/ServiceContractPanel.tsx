import { ChevronDown, ChevronRight, Code2, ArrowRight, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import type { ServiceContract, ServiceStatus } from '@/types'

interface Props {
  contract: ServiceContract
  status?: ServiceStatus
}

const STATUS_STYLE: Record<ServiceStatus, { icon: typeof CheckCircle2; className: string }> = {
  ACTIVE:      { icon: CheckCircle2,  className: 'bg-[hsl(var(--success)/0.12)] text-[hsl(var(--success))]' },
  REGISTERED:  { icon: CheckCircle2,  className: 'bg-[hsl(var(--success)/0.12)] text-[hsl(var(--success))]' },
  DISABLED:    { icon: AlertTriangle, className: 'bg-[hsl(var(--warning)/0.12)] text-[hsl(var(--warning))]' },
  UNAVAILABLE: { icon: AlertTriangle, className: 'bg-[hsl(var(--warning)/0.12)] text-[hsl(var(--warning))]' },
  FAILED:      { icon: XCircle,       className: 'bg-[hsl(var(--danger)/0.12)] text-[hsl(var(--danger))]' },
  REMOVED:     { icon: XCircle,       className: 'bg-[hsl(var(--danger)/0.12)] text-[hsl(var(--danger))]' },
}

function ServiceStatusBadge({ status }: { status: ServiceStatus }) {
  const { icon: Icon, className } = STATUS_STYLE[status]
  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium',
      className,
    )}>
      <Icon size={10} />
      {status}
    </span>
  )
}

export function ServiceContractPanel({ contract, status }: Props) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="rounded-lg border border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-elevated))] p-4">
        <div className="flex items-center gap-2 mb-2">
          <Code2 size={15} className="text-[hsl(var(--accent))]" />
          <span className="text-sm font-semibold text-[hsl(var(--text))]">
            {contract.service_id}
          </span>
          {status && <ServiceStatusBadge status={status} />}
          <span className="text-xs font-mono text-[hsl(var(--text-subtle))] ml-auto">
            v{contract.version}
          </span>
        </div>
        <p className="text-xs text-[hsl(var(--text-muted))] mb-3">{contract.description}</p>

        {contract.capabilities.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <span className="text-[10px] text-[hsl(var(--text-subtle))] uppercase tracking-wide font-medium">
              Capabilities:
            </span>
            {contract.capabilities.map(cap => (
              <span key={cap} className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono
                bg-[hsl(var(--accent)/0.1)] text-[hsl(var(--accent))]">
                {cap}
              </span>
            ))}
          </div>
        )}

        {contract.dependencies.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10px] text-[hsl(var(--text-subtle))] uppercase tracking-wide font-medium">
              Dependências:
            </span>
            {contract.dependencies.map(d => (
              <span key={d} className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono
                bg-[hsl(var(--bg-subtle))] text-[hsl(var(--text-muted))]">
                {d}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Exports */}
      {contract.exports.length > 0 && (
        <div>
          <p className="text-[10px] font-medium uppercase tracking-widest text-[hsl(var(--text-subtle))] mb-2 px-1">
            Exports ({contract.exports.length})
          </p>
          <div className="space-y-2">
            {contract.exports.map(exp => (
              <ExportCard key={exp.name} exp={exp} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ExportCard({ exp }: { exp: ServiceContract['exports'][0] }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="rounded-lg border border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-elevated))] overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className={cn(
          'w-full flex items-center gap-2.5 px-4 py-3 text-left',
          'hover:bg-[hsl(var(--bg-subtle))] transition-colors',
        )}
      >
        {open
          ? <ChevronDown size={12} className="text-[hsl(var(--text-subtle))] flex-shrink-0" />
          : <ChevronRight size={12} className="text-[hsl(var(--text-subtle))] flex-shrink-0" />}
        <code className="text-xs font-mono text-[hsl(var(--accent))] font-medium">
          {exp.name}
        </code>
        <span className="text-xs text-[hsl(var(--text-muted))] truncate flex-1">
          — {exp.description}
        </span>
        {exp.returns && (
          <span className="flex items-center gap-1 text-[10px] font-mono text-[hsl(var(--text-subtle))] flex-shrink-0">
            <ArrowRight size={10} />
            {exp.returns.split(' ')[0]}
          </span>
        )}
      </button>

      {open && (
        <div className="px-4 pb-4 pt-1 border-t border-[hsl(var(--border-subtle))] space-y-3">
          {/* Parameters */}
          {exp.parameters.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-wide font-medium text-[hsl(var(--text-subtle))] mb-1.5">
                Parâmetros
              </p>
              <div className="rounded overflow-hidden border border-[hsl(var(--border-subtle))]">
                {exp.parameters.map((p, i) => (
                  <div key={p.name} className={cn(
                    'flex items-start gap-3 px-3 py-2 text-xs',
                    i < exp.parameters.length - 1 && 'border-b border-[hsl(var(--border-subtle))]',
                  )}>
                    <code className="font-mono text-[hsl(var(--accent))] flex-shrink-0">{p.name}</code>
                    <span className="font-mono text-[hsl(var(--text-subtle))] text-[10px] flex-shrink-0">
                      {p.type}{!p.required && '?'}
                    </span>
                    <span className="text-[hsl(var(--text-muted))] flex-1">{p.description}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Returns */}
          {exp.returns && (
            <div>
              <p className="text-[10px] uppercase tracking-wide font-medium text-[hsl(var(--text-subtle))] mb-1">
                Retorno
              </p>
              <p className="text-xs text-[hsl(var(--text-muted))]">{exp.returns}</p>
            </div>
          )}

          {/* Examples */}
          {exp.examples.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-wide font-medium text-[hsl(var(--text-subtle))] mb-1.5">
                Exemplos
              </p>
              <pre className="bg-[hsl(var(--bg))] border border-[hsl(var(--border-subtle))] rounded p-3 text-[11px] font-mono text-[hsl(var(--text-muted))] overflow-x-auto">
                {exp.examples.join('\n')}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
