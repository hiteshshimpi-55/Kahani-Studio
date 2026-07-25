import { FileText, Image, LoaderCircle, Plus, Volume2 } from 'lucide-react'
import { useEffect, useId, useRef, useState, type ReactNode } from 'react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export type AddAssetKind = 'context' | 'audio' | 'visual'

export type AddAssetAction = {
  kind: AddAssetKind
  label: string
  accept: string
  multiple?: boolean
  disabled?: boolean
  hint?: string
  onFiles: (files: File[]) => void | Promise<void>
}

type Props = {
  actions: AddAssetAction[]
  /** Compact circular trigger for chat composer */
  variant?: 'button' | 'icon'
  disabled?: boolean
  loading?: boolean
  label?: string
  className?: string
  align?: 'left' | 'right'
}

const ICONS: Record<AddAssetKind, typeof FileText> = {
  context: FileText,
  audio: Volume2,
  visual: Image,
}

export function AddAssetMenu({
  actions,
  variant = 'button',
  disabled = false,
  loading = false,
  label = 'Add',
  className,
  align = 'right',
}: Props) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const inputRefs = useRef<Record<string, HTMLInputElement | null>>({})
  const menuId = useId()

  useEffect(() => {
    if (!open) return
    const onDoc = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDoc)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const enabled = actions.filter((a) => !a.disabled)
  const triggerDisabled = disabled || loading || enabled.length === 0

  const pick = (action: AddAssetAction) => {
    if (action.disabled) return
    setOpen(false)
    inputRefs.current[action.kind]?.click()
  }

  let trigger: ReactNode
  if (variant === 'icon') {
    trigger = (
      <button
        type="button"
        title={label}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        disabled={triggerDisabled}
        onClick={() => setOpen((v) => !v)}
        className={cn(
          'flex h-9 w-9 items-center justify-center rounded-full text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)] disabled:opacity-40',
          className,
        )}
      >
        {loading ? (
          <LoaderCircle className="h-4 w-4 animate-spin" />
        ) : (
          <Plus className="h-4 w-4 stroke-[1.75]" />
        )}
      </button>
    )
  } else {
    trigger = (
      <Button
        type="button"
        disabled={triggerDisabled}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        onClick={() => setOpen((v) => !v)}
        className={className}
      >
        {loading ? (
          <LoaderCircle className="h-4 w-4 animate-spin" />
        ) : (
          <Plus className="h-4 w-4 stroke-[1.75]" />
        )}
        {label}
      </Button>
    )
  }

  return (
    <div ref={rootRef} className="relative inline-flex">
      {actions.map((action) => (
        <input
          key={action.kind}
          ref={(el) => {
            inputRefs.current[action.kind] = el
          }}
          type="file"
          className="sr-only"
          accept={action.accept}
          multiple={action.multiple}
          disabled={action.disabled || disabled || loading}
          onChange={(e) => {
            const list = e.target.files
            if (list?.length) void action.onFiles(Array.from(list))
            e.target.value = ''
          }}
        />
      ))}

      {trigger}

      {open ? (
        <div
          id={menuId}
          role="menu"
          className={cn(
            'absolute top-full z-40 mt-1.5 min-w-[200px] overflow-hidden rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] py-1 shadow-[0_12px_32px_rgba(15,23,42,0.14)]',
            align === 'right' ? 'right-0' : 'left-0',
          )}
        >
          {actions.map((action) => {
            const Icon = ICONS[action.kind]
            return (
              <button
                key={action.kind}
                type="button"
                role="menuitem"
                disabled={action.disabled}
                title={action.hint}
                onClick={() => pick(action)}
                className={cn(
                  'flex w-full items-start gap-2.5 px-3 py-2.5 text-left transition-colors',
                  action.disabled
                    ? 'cursor-not-allowed opacity-45'
                    : 'hover:bg-[var(--surface-1)]',
                )}
              >
                <Icon className="mt-0.5 h-4 w-4 shrink-0 stroke-[1.75] text-[var(--text-secondary)]" />
                <span className="min-w-0">
                  <span className="block text-[13px] font-medium text-[var(--text-primary)]">
                    {action.label}
                  </span>
                  {action.hint ? (
                    <span className="mt-0.5 block text-[11px] text-[var(--text-secondary)]">
                      {action.hint}
                    </span>
                  ) : null}
                </span>
              </button>
            )
          })}
        </div>
      ) : null}
    </div>
  )
}
