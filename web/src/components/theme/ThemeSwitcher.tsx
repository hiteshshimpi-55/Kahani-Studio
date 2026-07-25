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

/** Light / Dark segmented switch — no system mode, no quick-toggle row. */
export function ThemeSwitcher({ className }: Props) {
  const { resolvedTheme, setTheme } = useTheme()
  const mounted = useIsClient()
  const isDark = mounted && resolvedTheme === 'dark'

  return (
    <div className={cn('flex items-center justify-between gap-3', className)}>
      <span className="text-[13px] font-medium text-[var(--text-primary)]">Theme</span>
      <div
        role="group"
        aria-label="Theme"
        className="inline-flex h-8 items-center rounded-full bg-[var(--surface-1)] p-0.5"
      >
        <button
          type="button"
          disabled={!mounted}
          aria-pressed={!isDark}
          onClick={() => setTheme('light')}
          className={cn(
            'h-7 min-w-[52px] rounded-full px-2.5 text-[11px] font-semibold transition-colors',
            'border-0 outline-none focus-visible:outline-none',
            !isDark
              ? 'bg-[var(--surface-2)] text-[var(--text-primary)] shadow-sm'
              : 'bg-transparent text-[var(--text-muted)] hover:text-[var(--text-secondary)]',
          )}
        >
          Light
        </button>
        <button
          type="button"
          disabled={!mounted}
          aria-pressed={isDark}
          onClick={() => setTheme('dark')}
          className={cn(
            'h-7 min-w-[52px] rounded-full px-2.5 text-[11px] font-semibold transition-colors',
            'border-0 outline-none focus-visible:outline-none',
            isDark
              ? 'bg-[var(--surface-2)] text-[var(--text-primary)] shadow-sm'
              : 'bg-transparent text-[var(--text-muted)] hover:text-[var(--text-secondary)]',
          )}
        >
          Dark
        </button>
      </div>
    </div>
  )
}
