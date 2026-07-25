import { cn } from '@/lib/utils'

import type { EngagementReport } from '../types'

interface Props {
  engagement: EngagementReport
}

export function EngagementCard({ engagement }: Props) {
  return (
    <section className="rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-5 shadow-[var(--shadow-card)]">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-[15px] font-semibold text-[var(--text-primary)]">
          Uncalibrated cohort model
        </h3>
        <div className="flex items-center gap-2 text-[12px] text-[var(--text-secondary)]">
          <span className="rounded-[6px] bg-amber-500/15 px-2 py-0.5 text-amber-700">
            {engagement.calibration_status}
          </span>
          <span>{engagement.persona_count} personas</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-[13px]">
          <thead>
            <tr className="border-b border-[var(--folio-border)] text-[11px] tracking-wide text-[var(--text-muted)] uppercase">
              <th className="pb-2 pr-3 font-semibold">Part</th>
              <th className="pb-2 pr-3 font-semibold">Start rate</th>
              <th className="pb-2 pr-3 font-semibold">P(continue)</th>
              <th className="pb-2 pr-3 font-semibold">Top drop reason</th>
              <th className="pb-2 font-semibold">Fragile beat</th>
            </tr>
          </thead>
          <tbody>
            {engagement.funnel.map((part) => (
              <tr key={part.part} className="border-b border-[var(--folio-border)]">
                <td className="py-2.5 pr-3 font-mono text-[12px] text-[var(--text-primary)]">
                  P{part.part}
                </td>
                <td className="py-2.5 pr-3 text-[var(--text-primary)]">
                  {(part.start_rate * 100).toFixed(0)}%
                </td>
                <td className="py-2.5 pr-3">
                  <span
                    className={cn(
                      part.p_continue >= 0.6 && 'text-emerald-700',
                      part.p_continue >= 0.4 && part.p_continue < 0.6 && 'text-amber-700',
                      part.p_continue < 0.4 && 'text-destructive',
                    )}
                  >
                    {(part.p_continue * 100).toFixed(0)}%
                  </span>
                </td>
                <td className="py-2.5 pr-3 text-[12px] text-[var(--text-secondary)]">
                  {part.drop_reasons[0]?.replace(/_/g, ' ') || '—'}
                </td>
                <td className="py-2.5 font-mono text-[12px] text-[var(--text-muted)]">
                  {part.fragile_beats[0] || '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {engagement.funnel.some((f) => f.cohort_disagreements.length > 0) ? (
        <div className="mt-4 rounded-[8px] border border-amber-500/25 bg-amber-500/10 p-3">
          <p className="mb-1 text-[12px] font-medium text-amber-800">Cohort disagreements</p>
          {engagement.funnel
            .filter((f) => f.cohort_disagreements.length > 0)
            .map((f) => (
              <p key={f.part} className="text-[12px] text-amber-800/90">
                Part {f.part}: {f.cohort_disagreements[0]}
              </p>
            ))}
        </div>
      ) : null}
    </section>
  )
}
