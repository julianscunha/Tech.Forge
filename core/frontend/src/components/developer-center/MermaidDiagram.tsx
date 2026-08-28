import { useEffect, useRef, useState } from 'react'
import mermaid from 'mermaid'

let initialized = false

function ensureInitialized() {
  if (initialized) return
  mermaid.initialize({ startOnLoad: false, theme: 'neutral', securityLevel: 'strict' })
  initialized = true
}

interface Props {
  chart: string
}

export function MermaidDiagram({ chart }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    ensureInitialized()
    let cancelled = false
    mermaid.render(`dependency-graph-${Date.now()}`, chart)
      .then(({ svg }) => {
        if (!cancelled && containerRef.current) containerRef.current.innerHTML = svg
      })
      .catch((err) => { if (!cancelled) setError(String(err)) })
    return () => { cancelled = true }
  }, [chart])

  if (error) {
    return <p className="text-xs text-[hsl(var(--danger))]">Erro ao renderizar o grafo: {error}</p>
  }
  return <div ref={containerRef} className="overflow-x-auto" />
}
