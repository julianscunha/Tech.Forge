import { useState, type ReactNode } from 'react'
import { useDashboardLayoutStore, type DashboardCardId } from '@/store/dashboardLayout'
import { cn } from '@/lib/utils'

interface Props {
  id: DashboardCardId
  children: ReactNode
}

/** Wrapper de drag-and-drop HTML5 nativo — sem lib nova. Arrastar solta a
 * troca de posição imediatamente (sem preview fantasma customizado, o
 * navegador já cuida disso). */
export function DraggableCard({ id, children }: Props) {
  const moveCard = useDashboardLayoutStore((s) => s.moveCard)
  const [dragOver, setDragOver] = useState(false)

  return (
    <div
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData('text/x-dashboard-card', id)
        e.dataTransfer.effectAllowed = 'move'
      }}
      onDragOver={(e) => {
        e.preventDefault()
        setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragOver(false)
        const dragId = e.dataTransfer.getData('text/x-dashboard-card') as DashboardCardId
        if (dragId) moveCard(dragId, id)
      }}
      className={cn(
        'cursor-grab active:cursor-grabbing rounded-lg transition-shadow',
        dragOver && 'ring-2 ring-[hsl(var(--accent))]',
      )}
    >
      {children}
    </div>
  )
}
