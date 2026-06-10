/**
 * TechForge SDK — UI Components
 * ================================
 * Base React components for module frontends.
 * Import these instead of building your own to ensure visual consistency
 * with the Core design system.
 *
 * Usage:
 *   import { Card, PageHeader, DataTable, EmptyState } from '@techforge/sdk/components'
 */
import { type ReactNode, type ButtonHTMLAttributes, type InputHTMLAttributes } from 'react'

// ── cn utility (re-exported so modules don't need clsx) ───────────────────────
function cn(...classes: (string | undefined | false | null)[]): string {
  return classes.filter(Boolean).join(' ')
}

// ── Card ──────────────────────────────────────────────────────────────────────
interface CardProps {
  children: ReactNode
  className?: string
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

const paddingMap = { none: '', sm: 'p-3', md: 'p-4', lg: 'p-6' }

export function Card({ children, className, padding = 'md' }: CardProps) {
  return (
    <div className={cn(
      'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border-subtle))] rounded-lg',
      paddingMap[padding],
      className,
    )}>
      {children}
    </div>
  )
}

// ── PageHeader ────────────────────────────────────────────────────────────────
interface PageHeaderProps {
  title:       string
  description?: string
  actions?:    ReactNode
  className?:  string
}

export function PageHeader({ title, description, actions, className }: PageHeaderProps) {
  return (
    <div className={cn('flex items-start justify-between gap-4 mb-6', className)}>
      <div>
        <h1 className="text-lg font-semibold text-[hsl(var(--text))] tracking-tight">
          {title}
        </h1>
        {description && (
          <p className="text-sm text-[hsl(var(--text-muted))] mt-0.5">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}

// ── ModulePage wrapper ────────────────────────────────────────────────────────
interface ModulePageProps {
  children:  ReactNode
  className?: string
}

export function ModulePage({ children, className }: ModulePageProps) {
  return (
    <div className={cn('p-6 h-full overflow-y-auto animate-fade-in', className)}>
      {children}
    </div>
  )
}

// ── DataTable ─────────────────────────────────────────────────────────────────
interface Column<T> {
  key:      keyof T | string
  header:   string
  width?:   string
  render?:  (row: T) => ReactNode
  align?:   'left' | 'center' | 'right'
}

interface DataTableProps<T extends object> {
  columns:     Column<T>[]
  data:        T[]
  keyField:    keyof T
  emptyLabel?: string
  className?:  string
  loading?:    boolean
}

export function DataTable<T extends object>({
  columns, data, keyField, emptyLabel = 'Nenhum resultado.', className, loading,
}: DataTableProps<T>) {
  return (
    <div className={cn(
      'border border-[hsl(var(--border-subtle))] rounded-lg overflow-hidden',
      className,
    )}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-subtle))]">
            {columns.map((col) => (
              <th
                key={String(col.key)}
                style={{ width: col.width }}
                className={cn(
                  'px-4 py-2.5 text-[10px] font-medium uppercase tracking-widest',
                  'text-[hsl(var(--text-subtle))]',
                  col.align === 'right'  ? 'text-right'  : '',
                  col.align === 'center' ? 'text-center' : 'text-left',
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[hsl(var(--border-subtle))]">
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <tr key={i}>
                {columns.map((col) => (
                  <td key={String(col.key)} className="px-4 py-3">
                    <div className="h-3 rounded bg-[hsl(var(--bg-subtle))] animate-pulse" />
                  </td>
                ))}
              </tr>
            ))
          ) : data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-10 text-center text-sm text-[hsl(var(--text-subtle))]"
              >
                {emptyLabel}
              </td>
            </tr>
          ) : (
            data.map((row) => (
              <tr
                key={String(row[keyField])}
                className="hover:bg-[hsl(var(--bg-subtle))] transition-colors"
              >
                {columns.map((col) => (
                  <td
                    key={String(col.key)}
                    className={cn(
                      'px-4 py-3 text-[hsl(var(--text))]',
                      col.align === 'right'  ? 'text-right'  : '',
                      col.align === 'center' ? 'text-center' : '',
                    )}
                  >
                    {col.render
                      ? col.render(row)
                      : String(row[col.key as keyof T] ?? '—')}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}

// ── Form components ───────────────────────────────────────────────────────────
interface FormFieldProps {
  label:    string
  htmlFor?: string
  error?:   string
  hint?:    string
  required?: boolean
  children: ReactNode
}

export function FormField({ label, htmlFor, error, hint, required, children }: FormFieldProps) {
  return (
    <div className="space-y-1.5">
      <label
        htmlFor={htmlFor}
        className="block text-xs font-medium text-[hsl(var(--text-muted))]"
      >
        {label}
        {required && <span className="ml-0.5 text-[hsl(var(--danger))]">*</span>}
      </label>
      {children}
      {hint && !error && (
        <p className="text-[10px] text-[hsl(var(--text-subtle))]">{hint}</p>
      )}
      {error && (
        <p className="text-[10px] text-[hsl(var(--danger))]">{error}</p>
      )}
    </div>
  )
}

interface TextInputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean
}

export function TextInput({ error, className, ...props }: TextInputProps) {
  return (
    <input
      className={cn(
        'w-full px-3 py-1.5 rounded text-sm',
        'bg-[hsl(var(--bg-elevated))] border',
        error
          ? 'border-[hsl(var(--danger)/0.5)] focus:border-[hsl(var(--danger))]'
          : 'border-[hsl(var(--border-subtle))] focus:border-[hsl(var(--accent)/0.5)]',
        'text-[hsl(var(--text))] placeholder:text-[hsl(var(--text-subtle))]',
        'focus:outline-none transition-colors',
        className,
      )}
      {...props}
    />
  )
}

// ── Modal ─────────────────────────────────────────────────────────────────────
interface ModalProps {
  open:      boolean
  onClose:   () => void
  title:     string
  children:  ReactNode
  footer?:   ReactNode
  size?:     'sm' | 'md' | 'lg'
  className?: string
}

const sizeMap = { sm: 'max-w-sm', md: 'max-w-md', lg: 'max-w-2xl' }

export function Modal({ open, onClose, title, children, footer, size = 'md', className }: ModalProps) {
  if (!open) return null
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      <div
        className={cn(
          'relative z-10 w-full rounded-xl',
          'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border))]',
          'shadow-2xl animate-fade-in',
          sizeMap[size],
          className,
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[hsl(var(--border-subtle))]">
          <h2 className="text-sm font-semibold text-[hsl(var(--text))]">{title}</h2>
          <button
            onClick={onClose}
            className="w-6 h-6 flex items-center justify-center rounded text-[hsl(var(--text-muted))]
              hover:text-[hsl(var(--text))] hover:bg-[hsl(var(--bg-subtle))] transition-colors text-lg leading-none"
          >
            ×
          </button>
        </div>
        {/* Body */}
        <div className="px-5 py-4">{children}</div>
        {/* Footer */}
        {footer && (
          <div className="px-5 py-3 border-t border-[hsl(var(--border-subtle))] flex items-center justify-end gap-2">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Button ────────────────────────────────────────────────────────────────────
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?:    'sm' | 'md'
  loading?: boolean
  children: ReactNode
}

const variantMap = {
  primary:   'bg-[hsl(var(--accent))] text-white hover:bg-[hsl(var(--accent-hover))]',
  secondary: 'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border))] text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] hover:bg-[hsl(var(--bg-subtle))]',
  ghost:     'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] hover:bg-[hsl(var(--bg-subtle))]',
  danger:    'bg-[hsl(var(--danger)/0.1)] text-[hsl(var(--danger))] border border-[hsl(var(--danger)/0.3)] hover:bg-[hsl(var(--danger)/0.2)]',
}
const sizeButtonMap = { sm: 'px-2.5 py-1 text-xs', md: 'px-3 py-1.5 text-xs' }

export function Button({
  variant = 'secondary', size = 'md', loading, children, className, disabled, ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center gap-1.5 rounded font-medium transition-colors',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variantMap[variant],
        sizeButtonMap[size],
        className,
      )}
      {...props}
    >
      {loading && (
        <svg className="animate-spin w-3 h-3" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 100 16v-4l-3 3 3 3v-4a8 8 0 01-8-8z"/>
        </svg>
      )}
      {children}
    </button>
  )
}

// ── EmptyState ────────────────────────────────────────────────────────────────
interface EmptyStateProps {
  title:       string
  description?: string
  action?:     ReactNode
  icon?:       ReactNode
  className?:  string
}

export function EmptyState({ title, description, action, icon, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 text-center', className)}>
      {icon && (
        <div className="w-12 h-12 rounded-xl bg-[hsl(var(--bg-subtle))] flex items-center justify-center mb-4 text-[hsl(var(--text-muted))]">
          {icon}
        </div>
      )}
      <p className="text-sm font-medium text-[hsl(var(--text))] mb-1">{title}</p>
      {description && (
        <p className="text-xs text-[hsl(var(--text-muted))] max-w-xs mb-4">{description}</p>
      )}
      {action}
    </div>
  )
}

// ── LoadingState ──────────────────────────────────────────────────────────────
interface LoadingStateProps {
  message?:  string
  className?: string
}

export function LoadingState({ message = 'Carregando…', className }: LoadingStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 gap-3', className)}>
      <div className="w-5 h-5 border-2 border-[hsl(var(--accent)/0.3)] border-t-[hsl(var(--accent))] rounded-full animate-spin" />
      <p className="text-xs text-[hsl(var(--text-muted))]">{message}</p>
    </div>
  )
}

// ── Notification toast ────────────────────────────────────────────────────────
interface NotificationToastProps {
  title:    string
  message?: string
  level?:   'info' | 'success' | 'warning' | 'error'
  onClose?: () => void
}

const levelToast = {
  info:    'border-l-4 border-l-[hsl(var(--accent))]',
  success: 'border-l-4 border-l-[hsl(var(--success))]',
  warning: 'border-l-4 border-l-[hsl(var(--warning))]',
  error:   'border-l-4 border-l-[hsl(var(--danger))]',
}

export function NotificationToast({
  title, message, level = 'info', onClose,
}: NotificationToastProps) {
  return (
    <div className={cn(
      'flex items-start gap-3 px-4 py-3 rounded-lg shadow-lg',
      'bg-[hsl(var(--bg-elevated))] border border-[hsl(var(--border))]',
      levelToast[level],
    )}>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-[hsl(var(--text))]">{title}</p>
        {message && <p className="text-xs text-[hsl(var(--text-muted))] mt-0.5">{message}</p>}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="text-[hsl(var(--text-subtle))] hover:text-[hsl(var(--text))] text-sm leading-none flex-shrink-0"
        >
          ×
        </button>
      )}
    </div>
  )
}

// ── Badge ─────────────────────────────────────────────────────────────────────
interface BadgeProps {
  children:   ReactNode
  variant?:   'default' | 'success' | 'warning' | 'danger' | 'accent'
  className?: string
}

const badgeVariant = {
  default: 'bg-[hsl(var(--bg-subtle))] text-[hsl(var(--text-muted))]',
  success: 'bg-[hsl(var(--success)/0.12)] text-[hsl(var(--success))]',
  warning: 'bg-[hsl(var(--warning)/0.12)] text-[hsl(var(--warning))]',
  danger:  'bg-[hsl(var(--danger)/0.12)] text-[hsl(var(--danger))]',
  accent:  'bg-[hsl(var(--accent-muted))] text-[hsl(var(--accent))]',
}

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span className={cn(
      'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium',
      badgeVariant[variant],
      className,
    )}>
      {children}
    </span>
  )
}
