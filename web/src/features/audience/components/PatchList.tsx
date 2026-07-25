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
  if (status === 'ACCEPTED')
    return <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-800">Accepted</span>
  if (status === 'REJECTED')
    return <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-800">Rejected</span>
  return <span className="rounded-full bg-stone-200 px-2 py-0.5 text-xs text-stone-600">Pending</span>
}

export function PatchList({ patches, onDecide }: Props) {
  if (!patches.length) return null

  return (
    <section className="rounded-lg border border-stone-300 bg-[#faf7f0] p-5">
      <h3 className="mb-4 text-lg font-medium">Proposed patches</h3>
      <p className="mb-4 text-xs text-stone-500">
        Structured edits with expected metric deltas. Accept or reject each — no auto-apply.
      </p>

      <div className="flex flex-col gap-3">
        {patches.map((patch) => (
          <div
            key={patch.id}
            className="rounded border border-stone-200 bg-white p-4"
          >
            <div className="mb-2 flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="rounded bg-stone-100 px-2 py-0.5 font-mono text-xs">
                  {patch.beat_id}
                </span>
                <span className="text-xs font-medium text-stone-700">
                  {TYPE_LABELS[patch.patch_type] || patch.patch_type}
                </span>
                <span className="text-xs text-stone-400">Part {patch.part}</span>
              </div>
              {statusBadge(patch.status)}
            </div>

            <p className="mb-2 text-sm text-stone-700">{patch.rationale}</p>

            {patch.expected_delta && (
              <div className="mb-3 flex gap-2 text-xs text-stone-500">
                {Object.entries(patch.expected_delta).map(([k, v]) => (
                  <span key={k} className="rounded bg-stone-100 px-2 py-0.5">
                    {k}: {v}
                  </span>
                ))}
              </div>
            )}

            {patch.status === 'PENDING' && (
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => onDecide(patch.id, true)}
                  className={cn(
                    'rounded border border-green-600 px-3 py-1 text-xs text-green-700',
                    'hover:bg-green-50',
                  )}
                >
                  Accept
                </button>
                <button
                  type="button"
                  onClick={() => onDecide(patch.id, false)}
                  className={cn(
                    'rounded border border-red-400 px-3 py-1 text-xs text-red-600',
                    'hover:bg-red-50',
                  )}
                >
                  Reject
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
