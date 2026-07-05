import { useEffect, useRef } from 'react'
import { marked } from 'marked'
import { cn } from '@/lib/utils'

// Configure marked for safe rendering
marked.setOptions({ breaks: true, gfm: true })

interface Props {
  content: string
  className?: string
}

export function MarkdownRenderer({ content, className }: Props) {
  const ref = useRef<HTMLDivElement>(null)

  const html = marked.parse(content) as string

  // Add copy buttons to code blocks after render
  useEffect(() => {
    if (!ref.current) return
    ref.current.querySelectorAll('pre').forEach((pre) => {
      if (pre.querySelector('.copy-btn')) return  // already has button

      const btn = document.createElement('button')
      btn.className = 'copy-btn'
      btn.textContent = 'Copy'
      btn.setAttribute('aria-label', 'Copy code')

      btn.addEventListener('click', () => {
        const code = pre.querySelector('code')?.textContent ?? ''
        navigator.clipboard.writeText(code).then(() => {
          btn.textContent = 'Copied!'
          setTimeout(() => { btn.textContent = 'Copy' }, 2000)
        })
      })

      pre.style.position = 'relative'
      pre.appendChild(btn)
    })
  }, [html])

  return (
    <div
      ref={ref}
      className={cn('prose-techforge', className)}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
