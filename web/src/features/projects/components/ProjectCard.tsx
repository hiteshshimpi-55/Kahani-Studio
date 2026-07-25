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
      to={`/projects/${project.id}/chat`}
      className="block rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-4 transition-colors hover:bg-[var(--surface-1)]"
    >
      <h3 className="text-[14px] font-semibold text-[var(--text-primary)]">{project.name}</h3>
      {project.description ? (
        <p className="mt-1.5 line-clamp-2 text-[13px] leading-snug text-[var(--text-secondary)]">
          {project.description}
        </p>
      ) : (
        <p className="mt-1.5 text-[13px] text-[var(--text-secondary)] italic">No description</p>
      )}
      <p className="mt-3 text-[11px] text-[var(--text-secondary)]">
        Updated {formatDate(project.updated_at)}
      </p>
    </Link>
  )
}
