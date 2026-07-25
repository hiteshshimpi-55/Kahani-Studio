import { useTheme } from 'next-themes'
import { useSyncExternalStore } from 'react'

import { cn } from '@/lib/utils'

const emptySubscribe = () => () => {}

function useIsClient() {
  return useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false,
  )
}

type Props = {
  className?: string
}

/** Light / Dark switch — no system, no separate quick toggle. */
export function ThemeSwitcher({ className }: Props) {
  const { resolvedTheme, setTheme } = useTheme()
  const mounted = useIsClient()
  const isDark = mounted && resolvedTheme === 'dark'

  return (
    <div className={cn('flex items-center justify-between gap-3', className)}>
      <span className="text-[13px] font-medium text-[var(--text-primary)]">Theme</span>
      <button
        type="button"
        role="switch"
        aria-checked={isDark}
        aria-label={isDark ? 'Dark theme' : 'Light theme'}
        disabled={!mounted}
        onClick={() => setTheme(isDark ? 'light' : 'dark')}
        className={cn(
          'relative inline-flex h-8 w-[88px] shrink-0 items-center rounded-full p-1 transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand)]/40',
          isDark ? 'bg-[var(--ink)]' : 'bg-[var(--surface-1)] ring-1 ring-[var(--folio-border)]',
        )}
      >
        <span
          className={cn(
            'absolute top-1 bottom-1 w-[calc(50%-4px)] rounded-full bg-[var(--surface-2)] shadow-sm transition-transform duration-200',
            isDark ? 'translate-x-[calc(100%+4px)]' : 'translate-x-0',
          )}
        />
        <span
          className={cn(
            'relative z-[1] flex w-1/2 items-center justify-center text-[11px] font-semibold transition-colors',
            !isDark ? 'text-[var(--text-primary)]' : 'text-[var(--text-muted)]',
          )}
        >
          Light
        </span>
        <span
          className={cn(
            'relative z-[1] flex w-1/2 items-center justify-center text-[11px] font-semibold transition-colors',
            isDark ? 'text-white' : 'text-[var(--text-muted)]',
          )}
        >
          Dark
        </span>
      </button>
    </div>
  )
}
