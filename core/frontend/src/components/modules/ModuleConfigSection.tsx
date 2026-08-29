import { useEffect, useState } from 'react'
import { moduleConfigApi } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { ModuleConfigField } from '@/types'

interface Props {
  moduleId: string
  fields: ModuleConfigField[]
}

/** Configuração de módulo (Fase 12 §10) — dentro de Module Details, não uma
 * página separada (spec §31: "aparecer preferencialmente Module Details →
 * Settings"). Só é renderizado quando o manifesto declara `configuration.fields`. */
export function ModuleConfigSection({ moduleId, fields }: Props) {
  const [values, setValues] = useState<Record<string, unknown>>({})
  const [status, setStatus] = useState<'idle' | 'loading' | 'saving' | 'saved' | 'error'>('loading')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setStatus('loading')
    moduleConfigApi.get(moduleId)
      .then((res) => { setValues(res.values); setStatus('idle') })
      .catch((err) => { setError(String(err.message ?? err)); setStatus('error') })
  }, [moduleId])

  function updateField(id: string, raw: string, type: ModuleConfigField['type']) {
    let parsed: unknown = raw
    if (type === 'integer') parsed = raw === '' ? '' : Number.parseInt(raw, 10)
    if (type === 'float') parsed = raw === '' ? '' : Number.parseFloat(raw)
    if (type === 'boolean') parsed = raw === 'true'
    setValues((prev) => ({ ...prev, [id]: parsed }))
  }

  async function handleSave() {
    setStatus('saving')
    setError(null)
    try {
      const res = await moduleConfigApi.put(moduleId, values)
      setValues(res.values)
      setStatus('saved')
    } catch (err) {
      setError(String((err as Error).message ?? err))
      setStatus('error')
    }
  }

  if (status === 'loading') {
    return <p className="text-xs text-[hsl(var(--text-muted))]">Carregando configuração…</p>
  }

  return (
    <div className="space-y-3">
      {fields.map((field) => (
        <div key={field.id} className="flex items-center justify-between gap-3">
          <label htmlFor={`cfg-${field.id}`} className="text-xs text-[hsl(var(--text-muted))] flex-shrink-0">
            {field.id}
          </label>
          {field.type === 'boolean' ? (
            <select
              id={`cfg-${field.id}`}
              value={String(values[field.id] ?? field.default ?? false)}
              onChange={(e) => updateField(field.id, e.target.value, field.type)}
              className="text-xs bg-[hsl(var(--bg))] border border-[hsl(var(--border-subtle))] rounded px-2 py-1"
            >
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          ) : (
            <input
              id={`cfg-${field.id}`}
              type={field.type === 'integer' || field.type === 'float' ? 'number' : 'text'}
              value={String(values[field.id] ?? '')}
              onChange={(e) => updateField(field.id, e.target.value, field.type)}
              className={cn(
                'text-xs font-mono bg-[hsl(var(--bg))] border border-[hsl(var(--border-subtle))]',
                'rounded px-2 py-1 w-28 text-right text-[hsl(var(--text))]'
              )}
            />
          )}
        </div>
      ))}

      {error && <p className="text-xs text-[hsl(var(--danger))]">{error}</p>}

      <button
        onClick={handleSave}
        disabled={status === 'saving'}
        className={cn(
          'w-full text-xs font-medium rounded px-3 py-1.5 transition-colors',
          'bg-[hsl(var(--accent))] text-white hover:opacity-90 disabled:opacity-50'
        )}
      >
        {status === 'saving' ? 'Salvando…' : status === 'saved' ? 'Salvo ✓' : 'Salvar'}
      </button>
    </div>
  )
}
