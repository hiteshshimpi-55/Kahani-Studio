import { Check, LoaderCircle } from 'lucide-react'

import type { StageStatus } from '@/features/projects/types'
import { cn } from '@/lib/utils'

const STEPS: Array<{ key: string; label: string; optional?: boolean }> = [
  { key: 'script', label: 'Script' },
  { key: 'audio', label: 'Audio' },
  { key: 'visuals', label: 'Visuals', optional: true },
  { key: 'cover_art', label: 'Cover' },
  { key: 'assembly', label: 'Assemble' },
]

function stepTone(status?: StageStatus | string | null): 'done' | 'active' | 'idle' | 'failed' {
  if (status === 'approved') return 'done'
  if (status === 'generating' || status === 'pending_approval') return 'active'
  if (status === 'failed' || status === 'rejected') return 'failed'
  return 'idle'
}

export function PipelineStepper({
  stageStatuses,
  currentStage,
}: {
  stageStatuses?: Partial<Record<string, StageStatus | string>> | null
  currentStage?: string | null
}) {
  const visibleSteps = STEPS.filter((step) => {
    if (!step.optional) return true
    const status = stageStatuses?.[step.key]
    return Boolean(status && status !== 'idle' && status !== 'rejected')
  })

  return (
    <ol className="flex flex-wrap items-center gap-2">
      {visibleSteps.map((step, idx) => {
        const status = stageStatuses?.[step.key]
        const tone = stepTone(status)
        const isCurrent = currentStage === step.key || currentStage === 'complete'
        return (
          <li key={step.key} className="flex items-center gap-2">
            <span
              className={cn(
                'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold tracking-wide uppercase',
                tone === 'done' && 'bg-emerald-500/15 text-emerald-700',
                tone === 'active' && 'bg-[var(--brand)]/15 text-[var(--brand)]',
                tone === 'failed' && 'bg-destructive/15 text-destructive',
                tone === 'idle' && 'bg-[var(--surface-1)] text-[var(--text-muted)]',
                isCurrent && tone === 'idle' && 'ring-1 ring-[var(--folio-border)]',
              )}
              title={status || 'idle'}
            >
              {tone === 'done' ? (
                <Check className="h-3 w-3" />
              ) : status === 'generating' ? (
                <LoaderCircle className="h-3 w-3 animate-spin" />
              ) : (
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-current opacity-70" />
              )}
              {step.label}
            </span>
            {idx < visibleSteps.length - 1 ? (
              <span className="text-[var(--text-muted)]" aria-hidden>
                →
              </span>
            ) : null}
          </li>
        )
      })}
    </ol>
  )
}
