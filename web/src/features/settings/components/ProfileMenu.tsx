import { useEffect, useId, useRef, useState } from 'react'

import { BrandMark } from '@/components/brand/BrandMark'
import { ThemeSwitcher } from '@/components/theme/ThemeSwitcher'
import { cn } from '@/lib/utils'

type Props = {
  collapsed?: boolean
  className?: string
}

/** Anchored profile menu (TCC-style) — no redirects. */
export function ProfileMenu({ collapsed, className }: Props) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const menuId = useId()

  useEffect(() => {
    if (!open) return
    const onPointer = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('mousedown', onPointer)
    window.addEventListener('keydown', onKey)
    return () => {
      window.removeEventListener('mousedown', onPointer)
      window.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <div ref={rootRef} className={cn('relative', className)}>
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        onClick={() => setOpen((v) => !v)}
        title="Kahani Studio"
        className={cn(
          'flex w-full items-center gap-2.5 rounded-[10px] transition-colors hover:bg-[var(--surface-1)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--folio-border-strong)]',
          collapsed ? 'justify-center p-2' : 'px-2 py-2',
        )}
      >
        <span className="flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full ring-1 ring-[var(--folio-border)]">
          <BrandMark size={32} className="rounded-full" />
        </span>
        {!collapsed && (
          <span className="min-w-0 flex-1 text-left">
            <span className="block truncate text-[13px] font-semibold leading-tight text-[var(--text-primary)]">
              Kahani Studio
            </span>
            <span className="mt-0.5 block truncate text-[11px] leading-tight text-[var(--text-secondary)]">
              maker@kahani.app
            </span>
          </span>
        )}
      </button>

      {open ? (
        <div
          id={menuId}
          role="menu"
          className={cn(
            'absolute z-[90] w-[280px] overflow-hidden rounded-[12px] border border-[var(--folio-border)] bg-[var(--surface-2)] shadow-[var(--shadow-card)]',
            collapsed ? 'bottom-0 left-[calc(100%+8px)]' : 'bottom-[calc(100%+8px)] left-0 right-0 w-auto min-w-[260px]',
          )}
        >
          <div className="flex items-center gap-3 border-b border-[var(--folio-border)] px-3.5 py-3">
            <BrandMark size={36} className="rounded-[8px]" />
            <div className="min-w-0">
              <p className="truncate text-[13px] font-semibold text-[var(--text-primary)]">
                Kahani Studio
              </p>
              <p className="truncate text-[11px] text-[var(--text-secondary)]">maker@kahani.app</p>
            </div>
          </div>

          <div className="border-b border-[var(--folio-border)] px-3.5 py-3">
            <ThemeSwitcher />
          </div>

          <div className="px-3.5 py-3">
            <p className="text-[11px] font-medium tracking-wide text-[var(--text-muted)] uppercase">
              About
            </p>
            <p className="mt-1.5 text-[12px] leading-5 text-[var(--text-secondary)]">
              Kahani Studio is an audio-first story production studio. Context extraction grounds
              the Script Writer agent so you can draft, revise, and publish serial audio stories.
            </p>
          </div>
        </div>
      ) : null}
    </div>
  )
}
