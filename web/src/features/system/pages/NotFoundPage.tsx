import { Link } from 'react-router-dom'

import { BrandMark } from '@/components/brand/BrandMark'
import { cn } from '@/lib/utils'

export type NotFoundKind = 'route' | 'project' | 'draft' | 'resource'

type Props = {
  kind?: NotFoundKind
  /** Quiet technical detail under the body copy */
  detail?: string | null
  className?: string
}

const COPY: Record<
  NotFoundKind,
  { cue: string; title: string; body: string; primaryTo: string; primaryLabel: string }
> = {
  route: {
    cue: '404',
    title: 'This scene isn’t on the reel',
    body: 'That path doesn’t exist in Kahani Studio. Head back to your projects and pick up where you left off.',
    primaryTo: '/',
    primaryLabel: 'All projects',
  },
  project: {
    cue: 'MISSING',
    title: 'Project not found',
    body: 'This project may have been deleted, or the link is wrong. Open your library to continue.',
    primaryTo: '/',
    primaryLabel: 'All projects',
  },
  draft: {
    cue: 'CUT',
    title: 'Draft not found',
    body: 'That script draft isn’t available. Open a project and choose a draft from the list.',
    primaryTo: '/',
    primaryLabel: 'All projects',
  },
  resource: {
    cue: '404',
    title: 'Nothing here',
    body: 'We couldn’t find what you asked for. Try another link or return to your projects.',
    primaryTo: '/',
    primaryLabel: 'All projects',
  },
}

/** Shared missing-resource / 404 composition — brand-first, folio + Pocket FM red. */
export function NotFoundView({ kind = 'route', detail, className }: Props) {
  const copy = COPY[kind]

  return (
    <div
      className={cn(
        'relative flex min-h-[min(70vh,640px)] w-full flex-col items-center justify-center overflow-hidden px-6 py-16',
        className,
      )}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background: `
            radial-gradient(ellipse 55% 45% at 50% 38%, rgba(230, 25, 77, 0.14), transparent 70%),
            radial-gradient(ellipse 40% 30% at 78% 72%, rgba(230, 25, 77, 0.06), transparent 65%)
          `,
        }}
      />

      <div className="not-found-enter relative z-[1] mx-auto flex w-full max-w-lg flex-col items-center text-center">
        <BrandMark size={40} className="mb-8 shadow-sm" />

        <p
          className="text-[11px] font-bold tracking-[0.28em] text-[var(--brand)] uppercase"
          style={{ fontFamily: "'Courier Prime', ui-monospace, monospace" }}
        >
          Kahani Studio
        </p>

        <p
          className="mt-5 select-none text-[clamp(4.5rem,14vw,7rem)] leading-none font-bold tracking-tight text-[var(--brand)]/90"
          style={{ fontFamily: "'Courier Prime', ui-monospace, monospace" }}
          aria-hidden
        >
          {copy.cue}
        </p>

        <div
          aria-hidden
          className="mt-3 mb-8 flex h-5 items-end justify-center gap-[3px]"
        >
          {[0.35, 0.7, 1, 0.55, 0.85, 0.4, 0.65].map((h, i) => (
            <span
              key={i}
              className="not-found-bar w-[3px] rounded-full bg-[var(--brand)]"
              style={{
                height: `${h * 100}%`,
                animationDelay: `${i * 0.08}s`,
              }}
            />
          ))}
        </div>

        <h1 className="text-[22px] font-semibold tracking-tight text-[var(--text-primary)] md:text-[26px]">
          {copy.title}
        </h1>
        <p className="mt-2 max-w-md text-[14px] leading-relaxed text-[var(--text-secondary)]">
          {copy.body}
        </p>
        {detail ? (
          <p
            className="mt-2 max-w-md text-[11px] text-[var(--text-muted)]"
            style={{ fontFamily: "'Courier Prime', ui-monospace, monospace" }}
          >
            {detail}
          </p>
        ) : null}

        <div className="mt-8 flex flex-wrap items-center justify-center gap-2">
          <Link
            to={copy.primaryTo}
            className="inline-flex h-9 items-center justify-center rounded-[6px] bg-[var(--brand)] px-3.5 text-[13px] font-medium text-white shadow-sm transition-colors hover:bg-[var(--brand-strong)] focus-visible:ring-2 focus-visible:ring-[var(--folio-border-strong)] focus-visible:outline-none"
          >
            {copy.primaryLabel}
          </Link>
          <Link
            to="/editor"
            className="inline-flex h-9 items-center justify-center rounded-[6px] px-3.5 text-[13px] font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)] focus-visible:ring-2 focus-visible:ring-[var(--folio-border-strong)] focus-visible:outline-none"
          >
            Open editor
          </Link>
        </div>
      </div>
    </div>
  )
}

export function NotFoundPage() {
  return <NotFoundView kind="route" />
}
