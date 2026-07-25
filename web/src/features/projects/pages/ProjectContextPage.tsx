import { Link, useParams } from 'react-router-dom'

import { KissaLoader } from '@/components/ui/kissa-loader'
import { ContextAttachmentsPanel } from '@/features/projects/components/ContextAttachmentsPanel'
import { useAttachments } from '@/features/projects/hooks/use-attachments'
import { useProject } from '@/features/projects/hooks/use-project'
import { NotFoundView } from '@/features/system/pages/NotFoundPage'

export function ProjectContextPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { project, loading, error } = useProject(projectId)
  const attachments = useAttachments(projectId)

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <KissaLoader label="Loading context…" />
      </div>
    )
  }
  if (error || !project) {
    return (
      <NotFoundView
        kind="project"
        detail={error && error !== 'Not found' && error !== 'Project not found' ? error : null}
      />
    )
  }

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-6">
        <p className="text-[12px] text-[var(--text-secondary)]">
          <Link to={`/projects/${project.id}/chat`} className="hover:text-[var(--brand)]">
            {project.name}
          </Link>
        </p>
        <h1 className="mt-1 text-[22px] font-semibold tracking-tight">Context</h1>
        <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
          Add briefs the agent should know. Files here ground every Generate in chat.
        </p>
      </div>
      <ContextAttachmentsPanel
        attachments={attachments.attachments}
        loading={attachments.loading}
        uploading={attachments.uploading}
        error={attachments.error}
        onUpload={attachments.upload}
        onDelete={attachments.remove}
      />
    </div>
  )
}
