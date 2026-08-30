import { useEffect, useState } from 'react'
import { Settings, Database, GitBranch, CheckCircle2, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { systemApi, platformConfigApi } from '@/lib/api'
import type { StorageStatus, MigrationsStatus, PlatformConfig } from '@/types'

/** Platform Settings (Fase 12 §31) — página leve, sem painel administrativo
 * grande: Storage Status, Migration Status, configuração efetiva (export). */
export function SettingsPage() {
  const [storage, setStorage] = useState<StorageStatus | null>(null)
  const [migrations, setMigrations] = useState<MigrationsStatus | null>(null)
  const [config, setConfig] = useState<PlatformConfig | null>(null)

  useEffect(() => {
    systemApi.storageStatus().then(setStorage).catch(() => setStorage(null))
    systemApi.migrationsStatus().then(setMigrations).catch(() => setMigrations(null))
    platformConfigApi.get().then(setConfig).catch(() => setConfig(null))
  }, [])

  return (
    <div className="max-w-3xl mx-auto px-6 pt-4 pb-6 space-y-6">
      <div className="flex items-center gap-2">
        <Settings size={18} className="text-[hsl(var(--accent))]" />
        <h1 className="text-lg font-semibold text-[hsl(var(--text))]">Configurações</h1>
      </div>

      <Card icon={Database} title="Storage Status">
        {storage ? (
          <>
            <StatusRow label="Banco de dados" ok={storage.database} />
            <StatusRow label="Gravável" ok={storage.writable} />
          </>
        ) : (
          <p className="text-xs text-[hsl(var(--text-muted))]">Indisponível.</p>
        )}
      </Card>

      <Card icon={GitBranch} title="Migration Status">
        {migrations ? (
          <>
            <Row label="Head" value={migrations.head ?? '—'} />
            <Row label="Atual" value={migrations.current ?? '(nenhuma aplicada)'} />
            <StatusRow label="Em dia" ok={migrations.up_to_date} />
          </>
        ) : (
          <p className="text-xs text-[hsl(var(--text-muted))]">Indisponível.</p>
        )}
      </Card>

      <Card icon={Settings} title="Configuração efetiva da plataforma">
        {config ? (
          <pre className={cn(
            'text-[10px] font-mono leading-relaxed',
            'bg-[hsl(var(--bg))] border border-[hsl(var(--border-subtle))]',
            'rounded p-3 overflow-x-auto whitespace-pre-wrap',
            'text-[hsl(var(--text-muted))]'
          )}>
            {JSON.stringify(config, null, 2)}
          </pre>
        ) : (
          <p className="text-xs text-[hsl(var(--text-muted))]">Indisponível.</p>
        )}
      </Card>
    </div>
  )
}

function Card({ icon: Icon, title, children }: { icon: typeof Settings; title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-elevated))] p-4 space-y-2">
      <div className="flex items-center gap-2 mb-1">
        <Icon size={14} className="text-[hsl(var(--text-muted))]" />
        <h2 className="text-xs font-semibold uppercase tracking-wide text-[hsl(var(--text-muted))]">{title}</h2>
      </div>
      {children}
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-[hsl(var(--text-muted))]">{label}</span>
      <span className="font-mono text-[hsl(var(--text))]">{value}</span>
    </div>
  )
}

function StatusRow({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-[hsl(var(--text-muted))]">{label}</span>
      {ok ? (
        <span className="flex items-center gap-1 text-[hsl(var(--success))]">
          <CheckCircle2 size={12} /> ok
        </span>
      ) : (
        <span className="flex items-center gap-1 text-[hsl(var(--danger))]">
          <XCircle size={12} /> erro
        </span>
      )}
    </div>
  )
}
