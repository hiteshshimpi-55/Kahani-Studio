import { Link, useParams } from 'react-router-dom'

import { AddAssetMenu } from '@/components/AddAssetMenu'
import { ListingShell, PageHeader } from '@/components/layout/PageHeader'
import { KissaLoader } from '@/components/ui/kissa-loader'
import { CastPanel } from '@/features/projects/components/CastPanel'
import { ContextAttachmentsPanel } from '@/features/projects/components/ContextAttachmentsPanel'
import { EpisodesPanel } from '@/features/projects/components/EpisodesPanel'
import { useAttachments } from '@/features/projects/hooks/use-attachments'
import { useProject } from '@/features/projects/hooks/use-project'
import {
  useStoryCast,
  useStoryEpisodes,
} from '@/features/projects/hooks/use-story-context'
import { NotFoundView } from '@/features/system/pages/NotFoundPage'

export function ProjectContextPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { project, loading, error } = useProject(projectId)
  const attachments = useAttachments(projectId)
  const cast = useStoryCast(projectId)
  const episodes = useStoryEpisodes(projectId)

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <KissaLoader label="Loading story bible…" />
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
        title="Story Bible"
        description="Documents, cast, and episodes that ground every Generate in chat."
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
                label: 'Add document',
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

      <div className="space-y-6">
        <section>
          <div className="mb-3">
            <h2 className="text-[14px] font-semibold text-[var(--text-primary)]">Documents</h2>
            <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
              Briefs and research files retrieved into each episode.
            </p>
          </div>
          <ContextAttachmentsPanel
            attachments={attachments.attachments}
            loading={attachments.loading}
            uploading={attachments.uploading}
            error={attachments.error}
            onUpload={attachments.upload}
            onDelete={attachments.remove}
            showDropzone={false}
          />
        </section>

        <CastPanel
          characters={cast.characters}
          loading={cast.loading}
          error={cast.error}
          onUpdate={cast.update}
          onDelete={cast.remove}
        />

        <EpisodesPanel
          projectId={project.id}
          episodes={episodes.episodes}
          loading={episodes.loading}
          error={episodes.error}
          onPin={episodes.pin}
        />
      </div>
    </ListingShell>
  )
}
