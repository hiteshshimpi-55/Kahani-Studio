import { cn } from '@/lib/utils'

type Props = {
  label?: string
  className?: string
  size?: 'sm' | 'md' | 'lg'
}

const sizes = {
  sm: { box: 28, bar: 3 },
  md: { box: 40, bar: 4 },
  lg: { box: 52, bar: 5 },
} as const

/** Equalizer-style loader (no logo, no broadcast waves). */
export function KissaLoader({ label = 'Loading…', className, size = 'md' }: Props) {
  const { box, bar } = sizes[size]

  return (
    <div
      className={cn('flex flex-col items-center justify-center gap-3', className)}
      role="status"
      aria-live="polite"
    >
      <div
        className="kahani-loader-bars"
        style={{ height: box * 0.55, gap: bar }}
        aria-hidden
      >
        <i style={{ width: bar }} />
        <i style={{ width: bar }} />
        <i style={{ width: bar }} />
        <i style={{ width: bar }} />
      </div>
      {label ? (
        <p className="text-[12px] font-medium tracking-wide text-[var(--text-secondary)]">{label}</p>
      ) : null}
    </div>
  )
}
