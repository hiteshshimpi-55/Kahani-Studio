import { ExternalLink } from 'lucide-react'

import type { PitchResearchMeta, ResearchSource } from '../types'

type Props = {
  sources: ResearchSource[]
  research?: PitchResearchMeta | null
}

export function ResearchSourcesCard({ sources, research }: Props) {
  if (!sources.length) return null

  return (
    <div className="mt-3 overflow-hidden rounded-[14px] border border-[var(--folio-border)] bg-[var(--surface-1)]/60">
      <div className="flex flex-wrap items-center gap-2 border-b border-[var(--folio-border)] px-3.5 py-2.5">
        <p className="text-[11px] font-semibold tracking-[0.12em] text-[var(--text-muted)] uppercase">
          Sources
        </p>
        {research?.tavily ? (
          <span className="text-[11px] text-[var(--text-secondary)]">
            Discovery tool
            {research.topic ? (
              <span className="text-[var(--text-muted)]"> · {research.topic}</span>
            ) : null}
          </span>
        ) : null}
      </div>
      <ul className="divide-y divide-[var(--folio-border)]">
        {sources.map((src, i) => (
          <li key={`${src.url}-${i}`}>
            <a
              href={src.url}
              target="_blank"
              rel="noreferrer"
              className="group flex gap-3 px-3.5 py-3 transition-colors hover:bg-[var(--surface-0)]"
            >
              <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--surface-2)] text-[10px] font-semibold text-[var(--text-muted)] ring-1 ring-[var(--folio-border)]">
                {i + 1}
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex items-start gap-1.5 text-[13px] font-medium text-[var(--text-primary)] group-hover:text-[var(--brand)]">
                  <span className="truncate">{src.title || src.url}</span>
                  <ExternalLink className="mt-0.5 h-3 w-3 shrink-0 opacity-50" />
                </span>
                {src.snippet ? (
                  <span className="mt-0.5 line-clamp-2 block text-[12px] leading-5 text-[var(--text-secondary)]">
                    {src.snippet}
                  </span>
                ) : null}
                <span className="mt-0.5 block truncate text-[11px] text-[var(--text-muted)]">
                  {src.url.replace(/^https?:\/\//, '')}
                </span>
              </span>
            </a>
          </li>
        ))}
      </ul>
    </div>
  )
}
