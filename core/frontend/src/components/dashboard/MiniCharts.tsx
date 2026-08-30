/** Mini gráficos SVG feitos à mão — sem dependência de charting nova,
 * proporcional a um widget pequeno que expande dentro de um card. */

export function MiniBar({ label, percent, valueLabel }: { label: string; percent: number; valueLabel: string }) {
  const clamped = Math.min(Math.max(percent, 0), 100)
  return (
    <div>
      <div className="flex justify-between text-[11px] text-[hsl(var(--text-muted))] mb-1">
        <span>{label}</span>
        <span className="font-mono tabular-nums">{valueLabel}</span>
      </div>
      <svg width="100%" height="8" viewBox="0 0 100 8" preserveAspectRatio="none" role="img" aria-label={`${label}: ${valueLabel}`}>
        <rect x="0" y="0" width="100" height="8" rx="4" fill="hsl(var(--bg-subtle))" />
        <rect x="0" y="0" width={clamped} height="8" rx="4" fill="hsl(var(--accent))" />
      </svg>
    </div>
  )
}

export function MiniPie({ usedPercent, label }: { usedPercent: number; label: string }) {
  const r = 16
  const circumference = 2 * Math.PI * r
  const clamped = Math.min(Math.max(usedPercent, 0), 100)
  const offset = circumference * (1 - clamped / 100)
  return (
    <div className="flex items-center gap-3">
      <svg width="40" height="40" viewBox="0 0 40 40" role="img" aria-label={label}>
        <circle cx="20" cy="20" r={r} fill="none" stroke="hsl(var(--bg-subtle))" strokeWidth="6" />
        <circle
          cx="20" cy="20" r={r} fill="none" stroke="hsl(var(--accent))" strokeWidth="6"
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round" transform="rotate(-90 20 20)"
        />
      </svg>
      <span className="text-[11px] text-[hsl(var(--text-muted))]">{label}</span>
    </div>
  )
}
