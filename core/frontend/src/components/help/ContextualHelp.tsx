/**
 * ContextualHelp — Fase 5 §13
 * Botão "?" que abre a documentação mapeada para o context_id da página.
 * Mapping declarativo em docs/context-map.yaml (resolvido pelo Core).
 */
import { useEffect, useState } from 'react'
import { X, BookOpen } from 'lucide-react'
import { cn } from '@/lib/utils'
import { MarkdownRenderer } from '@/components/developer-center/MarkdownRenderer'

interface ContextDoc {
  context_id: string
  doc_id: string
  title: string
}

// eslint-disable-next-line react-refresh/only-export-components -- hook colocado com o componente que o usa, abaixo
export function useContextHelp(contextId: string | undefined) {
  const [doc, setDoc] = useState<ContextDoc | null>(null)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!contextId) return
    fetch(`/api/v1/docs/context/${contextId}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(setDoc)
      .catch(() => setDoc(null))
  }, [contextId])

  return { doc, open, setOpen }
}

export function HelpDrawer({ contextId }: { contextId?: string }) {
  const { doc, open, setOpen } = useContextHelp(contextId)
  const [content, setContent] = useState<string>('')

  useEffect(() => {
    if (!open || !doc) return
    fetch(`/api/v1/docs/article/${doc.doc_id}`)
      .then((r) => r.json())
      .then((a) => setContent(a.content ?? ''))
      .catch(() => setContent('Não foi possível carregar a documentação.'))
  }, [open, doc])

  if (!doc) return null // página sem help mapeado → sem botão

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        aria-label={`Ajuda: ${doc.title}`}
        title="Ajuda"
        className={cn(
          'flex items-center justify-center w-7 h-7 rounded',
          'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
          'hover:bg-[hsl(var(--bg-subtle))] transition-colors'
        )}
      >
        <BookOpen size={14} />
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex justify-end"
          role="dialog"
          aria-label={`Ajuda: ${doc.title}`}
        >
          <div className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} />
          <aside className="relative w-full max-w-md h-full bg-[hsl(var(--bg-elevated))] shadow-xl flex flex-col border-l border-[hsl(var(--border-subtle))]">
            <div className="flex items-center justify-between px-4 py-3 border-b border-[hsl(var(--border-subtle))]">
              <span className="text-sm font-semibold">{doc.title}</span>
              <button onClick={() => setOpen(false)} aria-label="Fechar ajuda">
                <X size={16} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 max-w-none">
              <MarkdownRenderer content={content} />
            </div>
          </aside>
        </div>
      )}
    </>
  )
}
