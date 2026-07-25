import { Link } from 'react-router-dom'
import { Pin } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

import type { ScriptSummary } from '../types'

interface Props {
  episodes: ScriptSummary[]
  loading: boolean
  error: string | null
  projectId: string
  onPin: (scriptId: string, pinned: boolean) => Promise<void>
}

export function EpisodesPanel({
  episodes,
  loading,
  error,
  projectId,
  onPin,
}: Props) {
  return (
    <section className="rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-5">
      <div className="mb-4">
        <h2 className="text-[14px] font-semibold text-[var(--text-primary)]">Episodes</h2>
        <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
          Saved drafts become continuity. The latest episode always grounds the next Generate;
          pin older ones to keep them in context.
        </p>
      </div>

      {error ? (
        <p className="mb-3 text-[13px] text-[var(--danger)]">{error}</p>
      ) : null}

      {loading && episodes.length === 0 ? (
        <p className="text-[13px] text-[var(--text-secondary)]">Loading episodes…</p>
      ) : null}

      {!loading && episodes.length === 0 ? (
        <p className="text-[13px] text-[var(--text-secondary)]">
          No saved episodes yet. Generate in chat, then save as a draft.
        </p>
      ) : null}

      <ul className="space-y-3">
        {episodes.map((ep) => (
          <li
            key={ep.id}
            className="rounded-[8px] border border-[var(--folio-border)] bg-[var(--surface-0)] px-3 py-3"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <Link
                    to={`/projects/${projectId}/drafts?draft=${ep.id}`}
                    className="text-[14px] font-medium text-[var(--text-primary)] hover:text-[var(--brand)]"
                  >
                    {ep.part_number != null ? `Ep. ${ep.part_number}` : `v${ep.version}`}
                    {ep.title ? ` — ${ep.title}` : ''}
                  </Link>
                  {ep.is_latest_continuity ? (
                    <Badge tone="success">Latest continuity</Badge>
                  ) : null}
                  {ep.pinned && !ep.is_latest_continuity ? (
                    <Badge tone="warning">Pinned</Badge>
                  ) : null}
                </div>
                {ep.cliff_out ? (
                  <p className="mt-1 text-[12px] text-[var(--text-secondary)] line-clamp-2">
                    Cliff: {ep.cliff_out}
                  </p>
                ) : ep.prompt_snippet ? (
                  <p className="mt-1 text-[12px] text-[var(--text-secondary)] line-clamp-2">
                    {ep.prompt_snippet}
                  </p>
                ) : null}
              </div>
              {!ep.is_latest_continuity ? (
                <Button
                  type="button"
                  size="sm"
                  variant={ep.pinned ? 'secondary' : 'ghost'}
                  className="shrink-0"
                  onClick={() => void onPin(ep.id, !ep.pinned)}
                >
                  <Pin className="size-3.5" />
                  {ep.pinned ? 'Unpin' : 'Pin'}
                </Button>
              ) : null}
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
