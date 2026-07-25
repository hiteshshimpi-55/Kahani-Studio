import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'

import { CreateProjectDialog } from '../components/CreateProjectDialog'
import { ProjectCard } from '../components/ProjectCard'
import { useProjects } from '../hooks/use-projects'

export function ProjectsPage() {
  const { projects, loading, error, create } = useProjects()
  const [dialogOpen, setDialogOpen] = useState(false)
  const navigate = useNavigate()

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Projects</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Create a project, attach context, and generate audio scripts.
          </p>
        </div>
        <Button type="button" onClick={() => setDialogOpen(true)}>
          New project
        </Button>
      </div>

      {error ? <p className="mt-6 text-sm text-destructive">{error}</p> : null}

      {loading ? (
        <p className="mt-10 text-sm text-muted-foreground">Loading projects…</p>
      ) : projects.length === 0 ? (
        <div className="mt-16 flex flex-col items-center text-center">
          <p className="text-base font-medium text-foreground">No projects yet</p>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Start with a name and description. You can upload source notes on the next screen.
          </p>
          <Button type="button" className="mt-6" onClick={() => setDialogOpen(true)}>
            Create your first project
          </Button>
        </div>
      ) : (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} />
          ))}
        </div>
      )}

      <CreateProjectDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onCreate={async (input) => {
          const project = await create(input)
          navigate(`/projects/${project.id}`)
          return project
        }}
      />
    </main>
  )
}
