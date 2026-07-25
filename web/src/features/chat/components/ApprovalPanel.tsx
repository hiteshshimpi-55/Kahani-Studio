import { useState } from 'react'
import { Check, LoaderCircle, RefreshCw, Pencil } from 'lucide-react'

import type { StageStatus } from '@/features/projects/types'

export function ApprovalPanel({
  stageLabel,
  status,
  busy,
  onApprove,
  onRegenerate,
  onRevise,
}: {
  stageLabel: string
  status?: StageStatus | string | null
  busy?: boolean
  onApprove: () => void | Promise<void>
  onRegenerate: () => void | Promise<void>
  onRevise: (notes: string) => void | Promise<void>
}) {
  const [revising, setRevising] = useState(false)
  const [notes, setNotes] = useState('')

  if (status === 'approved') {
    return (
      <p className="text-[12px] font-medium text-[var(--text-secondary)]">
        {stageLabel} approved
      </p>
    )
  }

  if (status === 'generating') {
    return (
      <p className="flex items-center gap-2 text-[13px] text-[var(--text-secondary)]">
        <LoaderCircle className="h-3.5 w-3.5 animate-spin text-[var(--brand)]" />
        Generating {stageLabel.toLowerCase()}…
      </p>
    )
  }

  if (status === 'failed') {
    return (
      <div className="space-y-2">
        <p className="text-[12px] text-destructive">{stageLabel} failed — try again.</p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy}
            className="inline-flex items-center gap-1.5 rounded-[8px] border border-[var(--folio-border)] bg-[var(--surface-1)] px-3 py-1.5 text-[12px] font-medium text-[var(--text-primary)] disabled:opacity-50"
            onClick={() => void onRegenerate()}
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Regenerate
          </button>
          <button
            type="button"
            disabled={busy}
            className="inline-flex items-center gap-1.5 rounded-[8px] border border-[var(--folio-border)] bg-[var(--surface-1)] px-3 py-1.5 text-[12px] font-medium text-[var(--text-primary)] disabled:opacity-50"
            onClick={() => setRevising((v) => !v)}
          >
            <Pencil className="h-3.5 w-3.5" />
            Revise
          </button>
        </div>
        {revising ? (
          <div className="space-y-2">
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder={`What should change about the ${stageLabel.toLowerCase()}?`}
              className="w-full resize-y rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-0)] px-3 py-2 text-[13px] text-[var(--text-primary)] outline-none focus:ring-2 focus:ring-[var(--brand)]/30"
            />
            <button
              type="button"
              disabled={busy || !notes.trim()}
              className="rounded-[8px] bg-[var(--brand)] px-3 py-1.5 text-[12px] font-medium text-white disabled:opacity-50"
              onClick={() => void onRevise(notes.trim())}
            >
              {busy ? 'Submitting…' : 'Submit revision'}
            </button>
          </div>
        ) : null}
      </div>
    )
  }

  if (status !== 'pending_approval') {
    return null
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy}
          className="inline-flex items-center gap-1.5 rounded-[8px] bg-[var(--brand)] px-3 py-1.5 text-[12px] font-medium text-white disabled:opacity-50"
          onClick={() => void onApprove()}
        >
          {busy ? (
            <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Check className="h-3.5 w-3.5" />
          )}
          Approve {stageLabel}
        </button>
        <button
          type="button"
          disabled={busy}
          className="inline-flex items-center gap-1.5 rounded-[8px] border border-[var(--folio-border)] bg-[var(--surface-1)] px-3 py-1.5 text-[12px] font-medium text-[var(--text-primary)] disabled:opacity-50"
          onClick={() => void onRegenerate()}
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Regenerate
        </button>
        <button
          type="button"
          disabled={busy}
          className="inline-flex items-center gap-1.5 rounded-[8px] border border-[var(--folio-border)] bg-[var(--surface-1)] px-3 py-1.5 text-[12px] font-medium text-[var(--text-primary)] disabled:opacity-50"
          onClick={() => setRevising((v) => !v)}
        >
          <Pencil className="h-3.5 w-3.5" />
          {revising ? 'Cancel revise' : 'Revise'}
        </button>
      </div>
      {revising ? (
        <div className="space-y-2">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            placeholder={`What should change about the ${stageLabel.toLowerCase()}?`}
            className="w-full resize-y rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-0)] px-3 py-2 text-[13px] text-[var(--text-primary)] outline-none focus:ring-2 focus:ring-[var(--brand)]/30"
          />
          <button
            type="button"
            disabled={busy || !notes.trim()}
            className="rounded-[8px] bg-[var(--brand)] px-3 py-1.5 text-[12px] font-medium text-white disabled:opacity-50"
            onClick={() => void onRevise(notes.trim())}
          >
            {busy ? 'Submitting…' : 'Submit revision'}
          </button>
        </div>
      ) : null}
    </div>
  )
}
