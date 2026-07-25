import { cn } from '@/lib/utils'

type Props = {
  label?: string
  className?: string
  size?: 'sm' | 'md' | 'lg'
}

const sizes = {
  sm: { box: 36, bar: 3 },
  md: { box: 48, bar: 4 },
  lg: { box: 64, bar: 5 },
} as const

/**
 * Story-broadcast loader — equalizer bars that rise like audio being written,
 * independent of the logo mark.
 */
export function KissaLoader({ label = 'Loading…', className, size = 'md' }: Props) {
  const { box, bar } = sizes[size]

  return (
    <div
      className={cn('flex flex-col items-center justify-center gap-3', className)}
      role="status"
      aria-live="polite"
    >
      <div
        className="kahani-loader"
        style={{ width: box, height: box }}
        aria-hidden
      >
        <span className="kahani-loader-arc kahani-loader-arc--1" />
        <span className="kahani-loader-arc kahani-loader-arc--2" />
        <span className="kahani-loader-arc kahani-loader-arc--3" />
        <span className="kahani-loader-bars" style={{ gap: bar }}>
          <i style={{ width: bar }} />
          <i style={{ width: bar }} />
          <i style={{ width: bar }} />
          <i style={{ width: bar }} />
        </span>
      </div>
      {label ? (
        <p className="text-[12px] font-medium tracking-wide text-[var(--text-secondary)]">{label}</p>
      ) : null}
    </div>
  )
}
