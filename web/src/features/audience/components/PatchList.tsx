import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

import type { Patch } from '../types'

interface Props {
  patches: Patch[]
  onDecide: (patchId: string, accepted: boolean) => void
}

const TYPE_LABELS: Record<string, string> = {
  shorten_cold_open: 'Shorten cold open',
  cliff_rewrite: 'Cliff rewrite',
  rebalance_pacing: 'Rebalance pacing',
  adjust_dialogue_ratio: 'Adjust dialogue ratio',
  raise_stakes: 'Raise stakes',
  add_tension_beat: 'Add tension beat',
  realign_genre_signals: 'Realign genre signals',
  strengthen_cold_open: 'Strengthen cold open',
  add_open_loop: 'Add open loop',
  resolve_cohort_split: 'Resolve cohort split',
}

function statusBadge(status: Patch['status']) {
  if (status === 'ACCEPTED') {
    return (
      <span className="rounded-[6px] bg-emerald-500/15 px-2 py-0.5 text-[11px] font-medium text-emerald-700">
        Accepted
      </span>
    )
  }
  if (status === 'REJECTED') {
    return (
      <span className="rounded-[6px] bg-destructive/15 px-2 py-0.5 text-[11px] font-medium text-destructive">
        Rejected
      </span>
    )
  }
  return (
    <span className="rounded-[6px] bg-[var(--surface-1)] px-2 py-0.5 text-[11px] font-medium text-[var(--text-secondary)]">
      Pending
    </span>
  )
}

export function PatchList({ patches, onDecide }: Props) {
  if (!patches.length) return null

  return (
    <section className="rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-5 shadow-[var(--shadow-card)]">
      <h3 className="mb-1 text-[15px] font-semibold text-[var(--text-primary)]">Proposed patches</h3>
      <p className="mb-4 text-[12px] text-[var(--text-secondary)]">
        Structured edits with expected metric deltas. Accept or reject each — no auto-apply.
      </p>

      <div className="flex flex-col gap-3">
        {patches.map((patch) => (
          <div
            key={patch.id}
            className="rounded-[8px] border border-[var(--folio-border)] bg-[var(--surface-0)] p-4"
          >
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-[4px] bg-[var(--surface-1)] px-2 py-0.5 font-mono text-[11px] text-[var(--text-secondary)]">
                  {patch.beat_id}
                </span>
                <span className="text-[12px] font-medium text-[var(--text-primary)]">
                  {TYPE_LABELS[patch.patch_type] || patch.patch_type}
                </span>
                <span className="text-[11px] text-[var(--text-muted)]">Part {patch.part}</span>
              </div>
              {statusBadge(patch.status)}
            </div>

            <p className="mb-2 text-[13px] text-[var(--text-secondary)]">{patch.rationale}</p>

            {patch.expected_delta ? (
              <div className="mb-3 flex flex-wrap gap-2 text-[11px] text-[var(--text-muted)]">
                {Object.entries(patch.expected_delta).map(([k, v]) => (
                  <span
                    key={k}
                    className="rounded-[4px] bg-[var(--surface-1)] px-2 py-0.5 text-[var(--text-secondary)]"
                  >
                    {k}: {v}
                  </span>
                ))}
              </div>
            ) : null}

            {patch.status === 'PENDING' ? (
              <div className="flex gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  className={cn(
                    'border border-emerald-600/40 text-emerald-700 hover:bg-emerald-500/10',
                  )}
                  onClick={() => onDecide(patch.id, true)}
                >
                  Accept
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  className="border border-destructive/40 text-destructive hover:bg-destructive/10"
                  onClick={() => onDecide(patch.id, false)}
                >
                  Reject
                </Button>
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  )
}
