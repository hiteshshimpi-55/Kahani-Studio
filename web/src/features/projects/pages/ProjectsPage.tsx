import { Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { Button } from '@/components/ui/button'

import { CreateProjectDialog } from '../components/CreateProjectDialog'
import { ProjectCard } from '../components/ProjectCard'
import { useProjects } from '../hooks/use-projects'

export function ProjectsPage() {
  const { projects, loading, error, create } = useProjects()
  const [dialogOpen, setDialogOpen] = useState(false)
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()

  useEffect(() => {
    if (params.get('new') === '1') {
      setDialogOpen(true)
      const next = new URLSearchParams(params)
      next.delete('new')
      setParams(next, { replace: true })
    }
  }, [params, setParams])

  return (
    <div className="mx-auto max-w-6xl">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-[22px] font-semibold tracking-tight text-[var(--text-primary)]">
            Projects
          </h1>
          <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
            Open a project chat to prompt the Script Writer agent.
          </p>
        </div>
        <Button type="button" onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 stroke-[1.75]" />
          New project
        </Button>
      </div>

      {error ? <p className="mt-6 text-[13px] text-destructive">{error}</p> : null}

      {loading ? (
        <p className="mt-10 text-[13px] text-[var(--text-secondary)]">Loading projects…</p>
      ) : projects.length === 0 ? (
        <div className="mt-16 flex flex-col items-center text-center">
          <p className="text-[15px] font-semibold text-[var(--text-primary)]">No projects yet</p>
          <p className="mt-1 max-w-sm text-[13px] text-[var(--text-secondary)]">
            Create a project, then chat with the agent to generate scripts.
          </p>
          <Button type="button" className="mt-6" onClick={() => setDialogOpen(true)}>
            <Plus className="h-4 w-4 stroke-[1.75]" />
            Create your first project
          </Button>
        </div>
      ) : (
        <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
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
          navigate(`/projects/${project.id}/chat`)
          return project
        }}
      />
    </div>
  )
}
