/**
 * TechForge Design System — Tokens
 * ==================================
 * Single source of truth for all visual decisions.
 * Inspired by VS Code, Linear, and Grafana.
 *
 * All values map to CSS custom properties defined in globals.css.
 * Use these constants in module frontends to stay in sync with the
 * Core design system automatically when themes change.
 */

// ── Spacing ───────────────────────────────────────────────────────────────────
export const spacing = {
  0:    '0px',
  0.5:  '2px',
  1:    '4px',
  1.5:  '6px',
  2:    '8px',
  2.5:  '10px',
  3:    '12px',
  4:    '16px',
  5:    '20px',
  6:    '24px',
  8:    '32px',
  10:   '40px',
  12:   '48px',
  16:   '64px',
} as const

// ── Border radius ─────────────────────────────────────────────────────────────
export const radius = {
  sm:  '4px',
  md:  '6px',
  lg:  '8px',
  xl:  '12px',
  full: '9999px',
} as const

// ── Font sizes ────────────────────────────────────────────────────────────────
export const fontSize = {
  '2xs': '10px',
  xs:    '11px',
  sm:    '12px',
  base:  '13px',
  md:    '14px',
  lg:    '16px',
  xl:    '18px',
  '2xl': '20px',
} as const

// ── Font weights ──────────────────────────────────────────────────────────────
export const fontWeight = {
  normal:   '400',
  medium:   '500',
  semibold: '600',
  bold:     '700',
} as const

// ── CSS variable references — used in Tailwind arbitrary values ───────────────
export const colors = {
  bg:          'hsl(var(--bg))',
  bgSubtle:    'hsl(var(--bg-subtle))',
  bgElevated:  'hsl(var(--bg-elevated))',
  border:      'hsl(var(--border))',
  borderSubtle:'hsl(var(--border-subtle))',
  text:        'hsl(var(--text))',
  textMuted:   'hsl(var(--text-muted))',
  textSubtle:  'hsl(var(--text-subtle))',
  accent:      'hsl(var(--accent))',
  accentHover: 'hsl(var(--accent-hover))',
  accentMuted: 'hsl(var(--accent-muted))',
  accentFg:    'hsl(var(--accent-fg))',
  success:     'hsl(var(--success))',
  warning:     'hsl(var(--warning))',
  danger:      'hsl(var(--danger))',
} as const

// ── Tailwind class shorthands used across all SDK components ──────────────────
// Import these in module components to get consistent styling without
// needing to remember the full CSS variable syntax.

export const cls = {
  // Surfaces
  surface:  'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border-subtle))] rounded-lg',
  card:     'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border-subtle))] rounded-lg p-4',

  // Text
  textPrimary:  'text-[hsl(var(--text))]',
  textMuted:    'text-[hsl(var(--text-muted))]',
  textSubtle:   'text-[hsl(var(--text-subtle))]',
  textAccent:   'text-[hsl(var(--accent))]',
  textDanger:   'text-[hsl(var(--danger))]',
  textWarning:  'text-[hsl(var(--warning))]',
  textSuccess:  'text-[hsl(var(--success))]',

  // Labels
  sectionLabel: 'text-[10px] font-medium uppercase tracking-widest text-[hsl(var(--text-subtle))]',
  fieldLabel:   'text-xs font-medium text-[hsl(var(--text-muted))]',

  // Interactive
  buttonPrimary: [
    'inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium',
    'bg-[hsl(var(--accent))] text-white',
    'hover:bg-[hsl(var(--accent-hover))] transition-colors',
    'disabled:opacity-50 disabled:cursor-not-allowed',
  ].join(' '),

  buttonSecondary: [
    'inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium',
    'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border))]',
    'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
    'hover:bg-[hsl(var(--bg-subtle))] transition-colors',
    'disabled:opacity-50 disabled:cursor-not-allowed',
  ].join(' '),

  buttonGhost: [
    'inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium',
    'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))]',
    'hover:bg-[hsl(var(--bg-subtle))] transition-colors',
  ].join(' '),

  // Input
  input: [
    'w-full px-3 py-1.5 rounded text-sm',
    'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border-subtle))]',
    'text-[hsl(var(--text))] placeholder:text-[hsl(var(--text-subtle))]',
    'focus:outline-none focus:border-[hsl(var(--accent)/0.5)]',
    'transition-colors',
  ].join(' '),

  // Focus
  focusRing: 'focus-visible:outline-2 focus-visible:outline-[hsl(var(--accent))] focus-visible:outline-offset-2',
} as const
