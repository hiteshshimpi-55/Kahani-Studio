import { Link, useParams } from 'react-router-dom'

import { AddAssetMenu } from '@/components/AddAssetMenu'
import { ListingShell, PageHeader } from '@/components/layout/PageHeader'
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
    <ListingShell maxWidth="3xl">
      <PageHeader
        title="Context"
        description="Add briefs the agent should know. Files here ground every Generate in chat."
        breadcrumb={
          <Link to={`/projects/${project.id}/chat`} className="hover:text-[var(--brand)]">
            {project.name}
          </Link>
        }
        actions={
          <AddAssetMenu
            loading={attachments.uploading}
            actions={[
              {
                kind: 'context',
                label: 'Add context',
                accept: '.md,.txt,.markdown,text/plain,text/markdown',
                multiple: true,
                hint: '.md or .txt for RAG',
                onFiles: async (files) => {
                  await attachments.upload(files)
                },
              },
            ]}
          />
        }
      />
      <ContextAttachmentsPanel
        attachments={attachments.attachments}
        loading={attachments.loading}
        uploading={attachments.uploading}
        error={attachments.error}
        onUpload={attachments.upload}
        onDelete={attachments.remove}
        showDropzone={false}
      />
    </ListingShell>
  )
}
