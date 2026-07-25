import type { AuditScore, StructuralAudit } from '../types'

interface Props {
  audit: StructuralAudit
}

function ScoreBar({ score }: { score: AuditScore }) {
  const pct = Math.round(score.score * 100)
  const color =
    score.score >= 0.7 ? 'bg-green-500' : score.score >= 0.5 ? 'bg-amber-500' : 'bg-red-500'

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium capitalize">{score.name.replace('_', ' ')}</span>
        <span className="text-stone-500">{pct}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-stone-200">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <p className="text-xs text-stone-500">{score.comment}</p>
    </div>
  )
}

export function AuditCard({ audit }: Props) {
  const overallPct = Math.round(audit.overall_score * 100)

  return (
    <section className="rounded-lg border border-stone-300 bg-[#faf7f0] p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-medium">Craft checklist</h3>
        <span className="rounded-full bg-stone-200 px-3 py-0.5 text-xs font-medium">
          Overall: {overallPct}%
        </span>
      </div>
      <div className="flex flex-col gap-4">
        <ScoreBar score={audit.hook_score} />
        <ScoreBar score={audit.pacing_score} />
        <ScoreBar score={audit.dialogue_score} />
        <ScoreBar score={audit.cliffhanger_score} />
      </div>
    </section>
  )
}
