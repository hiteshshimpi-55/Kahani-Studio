import { Link, useParams } from 'react-router-dom'

import { KissaLoader } from '@/components/ui/kissa-loader'
import { useProject } from '@/features/projects/hooks/use-project'

export function ProjectVisualsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { project, loading, error } = useProject(projectId)

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <KissaLoader label="Loading visuals…" />
      </div>
    )
  }
  if (error || !project) {
    return <p className="text-[13px] text-destructive">{error || 'Not found'}</p>
  }

  return (
    <div className="mx-auto max-w-3xl">
      <p className="text-[12px] text-[var(--text-secondary)]">
        <Link to={`/projects/${project.id}/chat`} className="hover:text-[var(--brand)]">
          {project.name}
        </Link>
      </p>
      <h1 className="mt-1 text-[22px] font-semibold tracking-tight">Visuals</h1>
      <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
        Companion frames appear after a draft is generated. Visuals agent wiring comes next.
      </p>
      <div className="mt-10 rounded-[10px] border border-dashed border-[var(--folio-border)] bg-[var(--surface-0)] p-10 text-center">
        <p className="text-[14px] font-medium">No visuals yet</p>
        <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
          Generate a script draft first, then visuals will attach to parts.
        </p>
        <Link
          to={`/projects/${project.id}/chat`}
          className="mt-3 inline-block text-[13px] font-medium text-[var(--brand)] hover:underline"
        >
          Open chat
        </Link>
      </div>
    </div>
  )
}
