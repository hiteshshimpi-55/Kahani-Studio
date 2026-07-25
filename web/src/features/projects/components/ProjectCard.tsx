import { Link } from 'react-router-dom'

import type { Project } from '../types'

function formatDate(iso: string) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(iso))
  } catch {
    return iso
  }
}

export function ProjectCard({ project }: { project: Project }) {
  return (
    <Link
      to={`/projects/${project.id}`}
      className="block rounded-lg border border-border bg-card p-5 transition-colors hover:border-primary/40 hover:bg-accent/40"
    >
      <h3 className="text-base font-semibold text-foreground">{project.name}</h3>
      {project.description ? (
        <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{project.description}</p>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground italic">No description</p>
      )}
      <p className="mt-4 text-xs text-muted-foreground">Updated {formatDate(project.updated_at)}</p>
    </Link>
  )
}
