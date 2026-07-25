import { ArrowLeft } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ContextAttachmentsPanel } from '../components/ContextAttachmentsPanel'
import { PromptComposer } from '../components/PromptComposer'
import { useAttachments } from '../hooks/use-attachments'
import { useProject } from '../hooks/use-project'
import { useProjectRun } from '../hooks/use-project-run'
import { NotFoundView } from '@/features/system/pages/NotFoundPage'

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { project, loading, error } = useProject(projectId)
  const attachments = useAttachments(projectId)
  const { run, busy, error: runError, start } = useProjectRun(projectId)
  const [prompt, setPrompt] = useState('')

  const indexedCount = attachments.attachments.filter((a) => a.index_status === 'indexed').length

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl">
        <p className="text-[13px] text-[var(--text-secondary)]">Loading project…</p>
      </div>
    )
  }

  if (error || !project) {
    return (
      <NotFoundView
        kind="project"
        detail={error && error !== 'Project not found' ? error : null}
      />
    )
  }

  return (
    <div className="mx-auto max-w-6xl">
      <Link
        to="/"
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Projects
      </Link>
      <div className="mt-3">
        <h1 className="text-[22px] font-semibold tracking-tight text-[var(--text-primary)]">
          {project.name}
        </h1>
        {project.description ? (
          <p className="mt-1.5 max-w-2xl text-[13px] text-[var(--text-secondary)]">
            {project.description}
          </p>
        ) : null}
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <PromptComposer
          prompt={prompt}
          onPromptChange={setPrompt}
          onGenerate={() => {
            void start({ prompt: prompt.trim() })
          }}
          busy={busy}
          warnNoContext={indexedCount === 0}
          run={run}
          error={runError}
          projectId={project.id}
        />
        <ContextAttachmentsPanel
          attachments={attachments.attachments}
          loading={attachments.loading}
          uploading={attachments.uploading}
          error={attachments.error}
          onUpload={attachments.upload}
          onDelete={attachments.remove}
        />
      </div>
    </div>
  )
}
