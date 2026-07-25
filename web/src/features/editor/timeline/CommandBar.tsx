import { useState } from 'react'

import { Button } from '@/components/ui/button'

import { applyTimelineCommand } from './commands'
import type { TimelineDoc } from './types'

type Props = {
  doc: TimelineDoc
  onChange: (doc: TimelineDoc) => void
  onRegen: (clipId: string) => void
}

export function TimelineCommandBar({ doc, onChange, onRegen }: Props) {
  const [value, setValue] = useState('')
  const [feedback, setFeedback] = useState<string | null>(null)

  const run = () => {
    const result = applyTimelineCommand(doc, value)
    setFeedback(result.message)
    if (result.doc) onChange(result.doc)
    if (result.regenClipId) onRegen(result.regenClipId)
    if (result.ok) setValue('')
  }

  return (
    <div className="rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-0)] p-3">
      <p className="text-[11px] font-medium text-[var(--text-secondary)]">Command</p>
      <div className="mt-1.5 flex gap-2">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') run()
          }}
          placeholder='mute music · move knock to 0:42 · regen riya line'
          className="h-9 flex-1 rounded-[8px] border border-[var(--folio-border)] bg-[var(--surface-1)] px-3 text-[13px] outline-none focus:border-[var(--brand)]"
        />
        <Button type="button" size="sm" onClick={run}>
          Run
        </Button>
      </div>
      {feedback ? (
        <p className="mt-1.5 text-[12px] text-[var(--text-secondary)]">{feedback}</p>
      ) : null}
    </div>
  )
}
