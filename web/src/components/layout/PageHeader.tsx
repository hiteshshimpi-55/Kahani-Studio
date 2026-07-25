import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

type Props = {
  title: string
  description?: string
  breadcrumb?: ReactNode
  actions?: ReactNode
  className?: string
  children?: ReactNode
}

/** Shared listing-page chrome: title, subtitle, optional + Add / actions. */
export function PageHeader({ title, description, breadcrumb, actions, className, children }: Props) {
  return (
    <div className={cn('mb-6', className)}>
      {breadcrumb ? <div className="mb-1 text-[12px] text-[var(--text-secondary)]">{breadcrumb}</div> : null}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-[22px] font-semibold tracking-tight text-[var(--text-primary)]">
            {title}
          </h1>
          {description ? (
            <p className="mt-1 text-[13px] text-[var(--text-secondary)]">{description}</p>
          ) : null}
        </div>
        {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
      </div>
      {children}
    </div>
  )
}

type ListingShellProps = {
  children: ReactNode
  maxWidth?: '3xl' | '4xl' | '5xl' | '6xl'
  className?: string
}

const MAX: Record<NonNullable<ListingShellProps['maxWidth']>, string> = {
  '3xl': 'max-w-3xl',
  '4xl': 'max-w-4xl',
  '5xl': 'max-w-5xl',
  '6xl': 'max-w-6xl',
}

export function ListingShell({ children, maxWidth = '4xl', className }: ListingShellProps) {
  return <div className={cn('mx-auto w-full', MAX[maxWidth], className)}>{children}</div>
}

type EmptyStateProps = {
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

export function ListingEmptyState({ title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'mt-4 flex flex-col items-center rounded-[10px] border border-dashed border-[var(--folio-border)] bg-[var(--surface-0)] px-6 py-12 text-center',
        className,
      )}
    >
      <p className="text-[14px] font-medium text-[var(--text-primary)]">{title}</p>
      {description ? (
        <p className="mt-1 max-w-sm text-[13px] text-[var(--text-secondary)]">{description}</p>
      ) : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  )
}
