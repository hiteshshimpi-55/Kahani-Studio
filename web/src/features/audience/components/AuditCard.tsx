import type { AuditScore, StructuralAudit } from '../types'

interface Props {
  audit: StructuralAudit
}

function ScoreBar({ score }: { score: AuditScore }) {
  const pct = Math.round(score.score * 100)
  const color =
    score.score >= 0.7
      ? 'bg-emerald-500'
      : score.score >= 0.5
        ? 'bg-amber-500'
        : 'bg-destructive'

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between text-[12px]">
        <span className="font-medium capitalize text-[var(--text-primary)]">
          {score.name.replace('_', ' ')}
        </span>
        <span className="text-[var(--text-muted)]">{pct}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-[var(--surface-1)]">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <p className="text-[12px] text-[var(--text-secondary)]">{score.comment}</p>
    </div>
  )
}

export function AuditCard({ audit }: Props) {
  const overallPct = Math.round(audit.overall_score * 100)

  return (
    <section className="rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-5 shadow-[var(--shadow-card)]">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h3 className="text-[15px] font-semibold text-[var(--text-primary)]">Craft checklist</h3>
        <span className="rounded-[6px] bg-[var(--surface-1)] px-3 py-0.5 text-[11px] font-medium text-[var(--text-secondary)]">
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
