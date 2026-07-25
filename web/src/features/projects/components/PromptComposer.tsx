import { Link } from 'react-router-dom'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

import type { ProjectRun } from '../types'

interface Props {
  prompt: string
  onPromptChange: (value: string) => void
  onGenerate: () => void
  busy: boolean
  warnNoContext: boolean
  run: ProjectRun | null
  error: string | null
  projectId: string
}

function runTone(status: ProjectRun['status']) {
  if (status === 'succeeded') return 'success' as const
  if (status === 'failed') return 'danger' as const
  if (status === 'running') return 'default' as const
  return 'warning' as const
}

export function PromptComposer({
  prompt,
  onPromptChange,
  onGenerate,
  busy,
  warnNoContext,
  run,
  error,
  projectId,
}: Props) {
  return (
    <section className="rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-5">
      <h2 className="text-[14px] font-semibold text-[var(--text-primary)]">Generate</h2>
      <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
        Describe the story you want. Context attachments ground the script.
      </p>

      <Textarea
        className="mt-4 min-h-[200px] text-[13px]"
        value={prompt}
        onChange={(e) => onPromptChange(e.target.value)}
        placeholder="Describe the story you want to generate…"
        disabled={busy}
      />

      {warnNoContext ? (
        <p className="mt-2 text-[12px] text-amber-700">
          No indexed context yet — generation will use the prompt only.
        </p>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <Button type="button" onClick={onGenerate} disabled={busy || !prompt.trim()}>
          {busy ? 'Generating…' : 'Generate'}
        </Button>
        {run ? <Badge tone={runTone(run.status)}>{run.status}</Badge> : null}
        {run?.status === 'succeeded' ? (
          <Link
            to={`/projects/${projectId}/scripts/latest`}
            className="text-[13px] font-medium text-[var(--brand)] hover:underline"
          >
            View script
          </Link>
        ) : null}
      </div>

      {run?.error || error ? (
        <p className="mt-3 text-[13px] text-destructive">{run?.error || error}</p>
      ) : null}
    </section>
  )
}
