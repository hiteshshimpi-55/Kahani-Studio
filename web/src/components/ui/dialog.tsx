import { cn } from '@/lib/utils'
import type { ReactNode } from 'react'
import { useEffect } from 'react'
import { createPortal } from 'react-dom'

interface DialogProps {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  children: ReactNode
  className?: string
}

/** Inline filters survive Lightning CSS minify (prod was dropping backdrop-filter). */
const BACKDROP_STYLE_LIGHT = {
  backgroundColor: 'rgba(28, 25, 23, 0.42)',
  backdropFilter: 'blur(16px) saturate(1.25)',
  WebkitBackdropFilter: 'blur(16px) saturate(1.25)',
} as const

const BACKDROP_STYLE_DARK = {
  backgroundColor: 'rgba(0, 0, 0, 0.55)',
  backdropFilter: 'blur(18px) saturate(1.3)',
  WebkitBackdropFilter: 'blur(18px) saturate(1.3)',
} as const

export function Dialog({ open, onClose, title, description, children, className }: DialogProps) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = prev
      window.removeEventListener('keydown', onKey)
    }
  }, [open, onClose])

  if (!open) return null

  const isDark =
    typeof document !== 'undefined' && document.documentElement.classList.contains('dark')

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Blur on a plain div — <button> + backdrop-filter is broken in several engines */}
      <div
        className="absolute inset-0"
        style={isDark ? BACKDROP_STYLE_DARK : BACKDROP_STYLE_LIGHT}
        aria-hidden
      />
      <button
        type="button"
        aria-label="Close dialog"
        className="absolute inset-0 z-[1] cursor-default bg-transparent"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        className={cn(
          'relative z-10 w-full max-w-md rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-6 shadow-lg',
          className,
        )}
      >
        <h2 id="dialog-title" className="text-[16px] font-semibold text-[var(--text-primary)]">
          {title}
        </h2>
        {description ? (
          <p className="mt-1 text-[13px] text-[var(--text-secondary)]">{description}</p>
        ) : null}
        <div className="mt-4">{children}</div>
      </div>
    </div>,
    document.body,
  )
}
