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
    <section className="rounded-lg border border-border bg-card p-5">
      <h2 className="text-base font-semibold">Generate</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Describe the story you want. Context attachments are retrieved to ground the script.
      </p>

      <Textarea
        className="mt-4 min-h-[200px]"
        value={prompt}
        onChange={(e) => onPromptChange(e.target.value)}
        placeholder="Describe the story you want to generate…"
        disabled={busy}
      />

      {warnNoContext ? (
        <p className="mt-2 text-sm text-amber-700">
          No indexed context yet — generation will use the prompt only.
        </p>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <Button
          type="button"
          onClick={onGenerate}
          disabled={busy || !prompt.trim()}
        >
          {busy ? 'Generating…' : 'Generate'}
        </Button>
        {run ? <Badge tone={runTone(run.status)}>{run.status}</Badge> : null}
        {run?.status === 'succeeded' ? (
          <Link
            to={`/projects/${projectId}/scripts/latest`}
            className="text-sm font-medium text-primary hover:underline"
          >
            View script
          </Link>
        ) : null}
      </div>

      {run?.error || error ? (
        <p className="mt-3 text-sm text-destructive">{run?.error || error}</p>
      ) : null}
    </section>
  )
}
