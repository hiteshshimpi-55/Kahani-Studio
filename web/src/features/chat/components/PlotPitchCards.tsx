import { Sparkles } from 'lucide-react'

import type { PlotPitch } from '../types'

type Props = {
  pitches: PlotPitch[]
  onPick?: (pitch: PlotPitch, index: number) => void
  disabled?: boolean
}

export function PlotPitchCards({ pitches, onPick, disabled }: Props) {
  if (!pitches.length) return null

  return (
    <div className="chat-tool-enter mt-4 space-y-3">
      {pitches.map((pitch, i) => (
        <button
          key={pitch.title}
          type="button"
          disabled={disabled}
          onClick={() => onPick?.(pitch, i)}
          className="group w-full rounded-[14px] border border-[var(--folio-border-strong)] bg-[var(--surface-2)] px-4 py-3.5 text-left shadow-[0_2px_8px_rgba(0,0,0,0.04)] transition-all hover:border-[var(--brand)]/40 hover:shadow-[0_4px_16px_rgba(230,25,77,0.08)] disabled:pointer-events-none disabled:opacity-60"
        >
          <div className="flex items-start gap-3">
            <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--brand)]/10 text-[11px] font-bold text-[var(--brand)]">
              {i + 1}
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-[14px] font-semibold leading-5 text-[var(--text-primary)] group-hover:text-[var(--brand)]">
                {pitch.title}
              </p>
              <p className="mt-1 text-[13px] leading-5 text-[var(--text-secondary)]">
                {pitch.logline}
              </p>
              <div className="mt-2 flex items-center gap-1.5">
                <Sparkles className="h-3 w-3 text-[var(--text-muted)]" />
                <span className="text-[11px] font-medium tracking-wide text-[var(--text-muted)] uppercase">
                  {pitch.tone}
                </span>
              </div>
            </div>
          </div>
        </button>
      ))}
    </div>
  )
}
