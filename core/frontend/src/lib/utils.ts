import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatBytes(bytes: number): string {
  if (bytes <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const exp = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  return `${(bytes / 1024 ** exp).toFixed(exp === 0 ? 0 : 1)} ${units[exp]}`
}

/** Formata um timestamp do backend (naive UTC, sem sufixo de fuso — ver
 * `server_default=func.now()` do SQLite) no fuso horário escolhido pelo
 * usuário. Sem o `Z`, o `Date` do JS trataria a string como hora local,
 * exibindo o valor UTC cru sem nenhuma conversão real. */
export function formatDateTime(iso: string | null | undefined, timeZone: string): string {
  if (!iso) return '—'
  const normalized = /Z$|[+-]\d{2}:\d{2}$/.test(iso) ? iso : `${iso}Z`
  const date = new Date(normalized)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString('pt-BR', { timeZone })
}
