import { Moon, Sun } from 'lucide-react'
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

export function ThemeToggle({ className }: { className?: string }) {
  const { resolvedTheme, setTheme } = useTheme()
  const mounted = useIsClient()

  if (!mounted) {
    return (
      <button
        type="button"
        className={cn(
          'flex h-9 w-9 items-center justify-center rounded-[6px] text-[var(--text-secondary)]',
          className,
        )}
        disabled
        aria-hidden
      />
    )
  }

  const isDark = resolvedTheme === 'dark'

  return (
    <button
      type="button"
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      className={cn(
        'flex h-9 w-9 items-center justify-center rounded-[6px] text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)]',
        className,
      )}
    >
      {isDark ? (
        <Sun className="h-[18px] w-[18px] stroke-[1.75]" />
      ) : (
        <Moon className="h-[18px] w-[18px] stroke-[1.75]" />
      )}
    </button>
  )
}
