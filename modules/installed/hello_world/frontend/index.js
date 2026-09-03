/**
 * hello_world — Frontend Entry Point
 * ======================================================
 * Module : hello_world
 * Name   : Hello World
 * Icon   : blocks
 * Color  : blue
 *
 * Micro-frontend puro (sem framework) — o Module Host só exige um
 * default export com render(container). JS já compilado (não .tsx):
 * o Core só serve .js/.mjs como asset de módulo (Fase 3 §11). Este
 * módulo é referência de arquitetura, sem lógica de negócio real.
 */

export const moduleConfig = {
  moduleId: 'hello_world',
  title: 'Hello World',
  icon: 'blocks',
  category: 'Examples',
  vendor: 'TechForge',
  route: '/modules/hello_world',
  description: 'Reference module — architecture validation only.',
}

function render(container) {
  container.innerHTML = ''
  container.style.cssText = 'padding:32px;font-family:inherit;'

  const header = document.createElement('div')
  header.style.cssText = 'display:flex;align-items:center;gap:12px;margin-bottom:16px;'

  const badge = document.createElement('div')
  badge.textContent = 'HW'
  badge.style.cssText =
    'width:40px;height:40px;border-radius:12px;background:hsl(var(--accent-muted));' +
    'color:hsl(var(--accent));display:flex;align-items:center;justify-content:center;' +
    'font-size:13px;font-weight:700;'

  const titleBlock = document.createElement('div')
  const title = document.createElement('h2')
  title.textContent = 'Hello World'
  title.style.cssText = 'font-size:15px;font-weight:600;color:hsl(var(--text));margin:0;'
  const subtitle = document.createElement('p')
  subtitle.textContent = 'TechForge · v1.0.0 · Examples'
  subtitle.style.cssText = 'font-size:11px;color:hsl(var(--text-muted));margin:2px 0 0;'
  titleBlock.appendChild(title)
  titleBlock.appendChild(subtitle)

  header.appendChild(badge)
  header.appendChild(titleBlock)

  const card = document.createElement('div')
  card.style.cssText =
    'border-radius:8px;border:1px solid hsl(var(--border-subtle));padding:16px;' +
    'background:hsl(var(--bg-elevated));margin-bottom:16px;'
  const cardText = document.createElement('p')
  cardText.style.cssText = 'font-size:11px;color:hsl(var(--text-muted));line-height:1.6;margin:0;'
  cardText.textContent =
    'This is the reference module for the TechForge Phase 3 architecture. ' +
    'It validates the SDK, CLI, and module contracts without implementing ' +
    'any real business logic.'
  card.appendChild(cardText)

  const code = document.createElement('code')
  code.textContent = 'module: hello_world · sdk: techforge-sdk@1.0.0 · cli: techforge-cli@1.0.0'
  code.style.cssText =
    'display:block;font-size:9px;font-family:monospace;color:hsl(var(--accent));' +
    'background:hsl(var(--bg-subtle));border-radius:4px;padding:10px 12px;'

  container.appendChild(header)
  container.appendChild(card)
  container.appendChild(code)
}

export default { render }
