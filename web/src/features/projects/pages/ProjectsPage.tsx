import { Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { ListingEmptyState, ListingShell, PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'

import { CreateProjectDialog } from '../components/CreateProjectDialog'
import { ProjectCard } from '../components/ProjectCard'
import { useProjects } from '../hooks/use-projects'

export function ProjectsPage() {
  const { projects, loading, error, create } = useProjects()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [initialPrompt, setInitialPrompt] = useState<string | undefined>()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()

  useEffect(() => {
    if (params.get('new') === '1') {
      const prompt = params.get('prompt') ?? undefined
      setInitialPrompt(prompt)
      setDialogOpen(true)
      const next = new URLSearchParams(params)
      next.delete('new')
      next.delete('prompt')
      setParams(next, { replace: true })
    }
  }, [params, setParams])

  return (
    <ListingShell maxWidth="6xl">
      <PageHeader
        title="Projects"
        description="Open a project chat to prompt the Script Writer agent."
        actions={
          <Button type="button" onClick={() => setDialogOpen(true)}>
            <Plus className="h-4 w-4 stroke-[1.75]" />
            New project
          </Button>
        }
      />

      {error ? <p className="mb-4 text-[13px] text-destructive">{error}</p> : null}

      {loading ? (
        <p className="text-[13px] text-[var(--text-secondary)]">Loading projects…</p>
      ) : projects.length === 0 ? (
        <ListingEmptyState
          title="No projects yet"
          description="Create a project, then chat with the agent to generate scripts."
          action={
            <Button type="button" onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4 stroke-[1.75]" />
              Create your first project
            </Button>
          }
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} />
          ))}
        </div>
      )}

      <CreateProjectDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        initialDescription={initialPrompt}
        onCreate={async (input) => {
          const project = await create(input)
          navigate(`/projects/${project.id}/chat`)
          return project
        }}
      />
    </ListingShell>
  )
}
