import type { EngagementReport } from '../types'

interface Props {
  engagement: EngagementReport
}

export function EngagementCard({ engagement }: Props) {
  return (
    <section className="rounded-lg border border-stone-300 bg-[#faf7f0] p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-medium">Uncalibrated cohort model</h3>
        <div className="flex items-center gap-2 text-xs text-stone-500">
          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-800">
            {engagement.calibration_status}
          </span>
          <span>{engagement.persona_count} personas</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-stone-200 text-xs text-stone-500">
              <th className="pb-2 pr-3 font-medium">Part</th>
              <th className="pb-2 pr-3 font-medium">Start rate</th>
              <th className="pb-2 pr-3 font-medium">P(continue)</th>
              <th className="pb-2 pr-3 font-medium">Top drop reason</th>
              <th className="pb-2 font-medium">Fragile beat</th>
            </tr>
          </thead>
          <tbody>
            {engagement.funnel.map((part) => (
              <tr key={part.part} className="border-b border-stone-100">
                <td className="py-2 pr-3 font-mono text-xs">P{part.part}</td>
                <td className="py-2 pr-3">{(part.start_rate * 100).toFixed(0)}%</td>
                <td className="py-2 pr-3">
                  <span
                    className={
                      part.p_continue >= 0.6
                        ? 'text-green-700'
                        : part.p_continue >= 0.4
                          ? 'text-amber-700'
                          : 'text-red-700'
                    }
                  >
                    {(part.p_continue * 100).toFixed(0)}%
                  </span>
                </td>
                <td className="py-2 pr-3 text-xs text-stone-600">
                  {part.drop_reasons[0]?.replace(/_/g, ' ') || '—'}
                </td>
                <td className="py-2 font-mono text-xs text-stone-500">
                  {part.fragile_beats[0] || '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {engagement.funnel.some((f) => f.cohort_disagreements.length > 0) && (
        <div className="mt-4 rounded border border-amber-200 bg-amber-50 p-3">
          <p className="mb-1 text-xs font-medium text-amber-800">Cohort disagreements</p>
          {engagement.funnel
            .filter((f) => f.cohort_disagreements.length > 0)
            .map((f) => (
              <p key={f.part} className="text-xs text-amber-700">
                Part {f.part}: {f.cohort_disagreements[0]}
              </p>
            ))}
        </div>
      )}
    </section>
  )
}
