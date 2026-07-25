import { cn } from '@/lib/utils'
import type { ReactNode } from 'react'
import { useEffect } from 'react'

interface DialogProps {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  children: ReactNode
  className?: string
}

export function Dialog({ open, onClose, title, description, children, className }: DialogProps) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Close dialog"
        className="absolute inset-0 bg-foreground/40"
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
    </div>
  )
}
