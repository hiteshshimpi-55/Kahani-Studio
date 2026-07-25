import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ContextAttachmentsPanel } from '../components/ContextAttachmentsPanel'
import { PromptComposer } from '../components/PromptComposer'
import { useAttachments } from '../hooks/use-attachments'
import { useProject } from '../hooks/use-project'
import { useProjectRun } from '../hooks/use-project-run'

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { project, loading, error } = useProject(projectId)
  const attachments = useAttachments(projectId)
  const { run, busy, error: runError, start } = useProjectRun(projectId)
  const [prompt, setPrompt] = useState('')

  const indexedCount = attachments.attachments.filter((a) => a.index_status === 'indexed').length

  if (loading) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-10">
        <p className="text-sm text-muted-foreground">Loading project…</p>
      </main>
    )
  }

  if (error || !project) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-10">
        <p className="text-sm text-destructive">{error || 'Project not found'}</p>
        <Link to="/" className="mt-4 inline-block text-sm text-primary hover:underline">
          Back to projects
        </Link>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <Link to="/" className="text-sm text-muted-foreground hover:text-primary">
        ← Projects
      </Link>
      <div className="mt-4">
        <h1 className="text-2xl font-bold tracking-tight">{project.name}</h1>
        {project.description ? (
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">{project.description}</p>
        ) : null}
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
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
    </main>
  )
}
