import { cn } from '@/lib/utils'
import type { HTMLAttributes } from 'react'

type Tone = 'default' | 'success' | 'warning' | 'danger' | 'muted'

const tones: Record<Tone, string> = {
  default: 'bg-primary/10 text-primary',
  success: 'bg-emerald-100 text-emerald-800',
  warning: 'bg-amber-100 text-amber-800',
  danger: 'bg-red-100 text-red-800',
  muted: 'bg-muted text-muted-foreground',
}

export function Badge({
  className,
  tone = 'default',
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-[4px] px-2 py-0.5 text-[11px] font-medium capitalize',
        tones[tone],
        className,
      )}
      {...props}
    />
  )
}
