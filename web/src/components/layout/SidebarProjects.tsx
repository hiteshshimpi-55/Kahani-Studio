import {
  ChevronDown,
  FileStack,
  FolderKanban,
  ImageIcon,
  MessageSquareText,
  Paperclip,
  Plus,
  Trash2,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { useProjects } from '@/features/projects/hooks/use-projects'
import { cn } from '@/lib/utils'

const PROJECT_LINKS = [
  { segment: 'chat', label: 'Chat', icon: MessageSquareText },
  { segment: 'context', label: 'Story Bible', icon: Paperclip },
  { segment: 'drafts', label: 'Drafts', icon: FileStack },
  { segment: 'visuals', label: 'Visuals', icon: ImageIcon },
] as const

type Props = {
  collapsed: boolean
}

export function SidebarProjects({ collapsed }: Props) {
  const { projects, loading, remove } = useProjects()
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const [sectionOpen, setSectionOpen] = useState(true)
  const [openProjectId, setOpenProjectId] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const activeProjectId = useMemo(() => {
    const m = pathname.match(/^\/projects\/([^/]+)/)
    return m?.[1] ?? null
  }, [pathname])

  useEffect(() => {
    if (activeProjectId) {
      setSectionOpen(true)
      setOpenProjectId(activeProjectId)
    }
  }, [activeProjectId])

  if (collapsed) {
    return (
      <Link
        to="/"
        title="Projects"
        className={cn(
          'flex items-center justify-center rounded-[6px] px-0 py-2 transition-colors',
          pathname === '/' || pathname.startsWith('/projects')
            ? 'bg-[var(--surface-1)] text-[var(--text-primary)]'
            : 'text-[var(--text-secondary)] hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)]',
        )}
      >
        <FolderKanban className="h-[18px] w-[18px] stroke-[1.75]" />
      </Link>
    )
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => setSectionOpen((v) => !v)}
        className={cn(
          'flex w-full items-center gap-2.5 rounded-[6px] px-2.5 py-2 text-[14px] font-medium transition-colors',
          'text-[var(--text-secondary)] hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)]',
        )}
      >
        <FolderKanban className="h-[18px] w-[18px] shrink-0 stroke-[1.75] opacity-80" />
        <span className="flex-1 text-left">Projects</span>
        <ChevronDown
          className={cn(
            'h-3.5 w-3.5 shrink-0 transition-transform',
            sectionOpen && 'rotate-180',
          )}
        />
      </button>

      {sectionOpen && (
        <div className="mb-1 ml-[1.625rem] space-y-0.5 border-l border-[var(--folio-border)] pl-2.5">
          <button
            type="button"
            onClick={() => navigate('/?new=1')}
            className="flex w-full items-center gap-2 rounded-[6px] px-2.5 py-1.5 text-[12px] font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)]"
          >
            <Plus className="h-3.5 w-3.5 stroke-[1.75]" />
            New project
          </button>

          {loading && (
            <p className="px-2.5 py-1.5 text-[11px] text-[var(--text-secondary)]">Loading…</p>
          )}

          {projects.map((project) => {
            const open = openProjectId === project.id
            const active = activeProjectId === project.id
            return (
              <div key={project.id}>
                <div
                  className={cn(
                    'group flex w-full items-center gap-0.5 rounded-[6px] transition-colors',
                    active
                      ? 'bg-[var(--surface-1)] text-[var(--text-primary)]'
                      : 'text-[var(--text-secondary)] hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)]',
                  )}
                >
                  <button
                    type="button"
                    onClick={() => {
                      setOpenProjectId(open ? null : project.id)
                      if (!open) navigate(`/projects/${project.id}/chat`)
                    }}
                    className="flex min-w-0 flex-1 items-center gap-1.5 px-2.5 py-1.5 text-left text-[12px] font-medium"
                  >
                    <ChevronDown
                      className={cn(
                        'h-3 w-3 shrink-0 transition-transform',
                        open && 'rotate-180',
                      )}
                    />
                    <span className="truncate">{project.name}</span>
                  </button>
                  <button
                    type="button"
                    title={`Delete ${project.name}`}
                    disabled={deletingId === project.id}
                    className="mr-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-[4px] text-[var(--text-muted)] opacity-0 transition-opacity group-hover:opacity-100 hover:bg-[var(--surface-0)] hover:text-destructive disabled:opacity-40"
                    onClick={(e) => {
                      e.stopPropagation()
                      if (!window.confirm(`Delete project “${project.name}”? This cannot be undone.`)) {
                        return
                      }
                      void (async () => {
                        setDeletingId(project.id)
                        try {
                          await remove(project.id)
                          if (activeProjectId === project.id) navigate('/')
                        } finally {
                          setDeletingId(null)
                        }
                      })()
                    }}
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>

                {open && (
                  <div className="ml-2 space-y-0.5 border-l border-[var(--folio-border)] py-0.5 pl-2">
                    {PROJECT_LINKS.map((item) => {
                      const to = `/projects/${project.id}/${item.segment}`
                      const itemActive = pathname === to || pathname.startsWith(`${to}/`)
                      const Icon = item.icon
                      return (
                        <Link
                          key={item.segment}
                          to={to}
                          className={cn(
                            'flex items-center gap-2 rounded-[6px] px-2 py-1.5 text-[12px] font-medium transition-colors',
                            itemActive
                              ? 'bg-[var(--surface-1)] text-[var(--text-primary)]'
                              : 'text-[var(--text-secondary)] hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)]',
                          )}
                        >
                          <Icon className="h-3.5 w-3.5 shrink-0 stroke-[1.75] opacity-80" />
                          <span className="truncate">{item.label}</span>
                        </Link>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
