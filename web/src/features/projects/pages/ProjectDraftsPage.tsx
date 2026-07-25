import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { KissaLoader } from '@/components/ui/kissa-loader'
import { getScript, listScripts } from '@/features/projects/api/projects-api'
import { useProject } from '@/features/projects/hooks/use-project'
import type { ScriptLatest, ScriptSummary } from '@/features/projects/types'
import { NotFoundView } from '@/features/system/pages/NotFoundPage'

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

export function ProjectDraftsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [params, setParams] = useSearchParams()
  const { project, loading, error } = useProject(projectId)
  const [drafts, setDrafts] = useState<ScriptSummary[]>([])
  const [selected, setSelected] = useState<ScriptLatest | null>(null)
  const [listError, setListError] = useState<string | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  useEffect(() => {
    if (!projectId) return
    void (async () => {
      try {
        const rows = await listScripts(projectId)
        setDrafts(rows)
        setListError(null)
        const want = params.get('draft') || rows[0]?.id
        if (want) {
          setDetailLoading(true)
          try {
            setSelected(await getScript(projectId, want))
            if (!params.get('draft') && rows[0]) {
              setParams({ draft: rows[0].id }, { replace: true })
            }
          } finally {
            setDetailLoading(false)
          }
        } else {
          setSelected(null)
        }
      } catch (e) {
        setDrafts([])
        setListError(e instanceof Error ? e.message : 'Failed to load drafts')
      }
    })()
  }, [projectId]) // eslint-disable-line react-hooks/exhaustive-deps -- intentional initial load

  async function selectDraft(id: string) {
    if (!projectId) return
    setParams({ draft: id }, { replace: true })
    setDetailLoading(true)
    try {
      setSelected(await getScript(projectId, id))
    } finally {
      setDetailLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <KissaLoader label="Loading drafts…" />
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
    <div className="mx-auto max-w-5xl">
      <p className="text-[12px] text-[var(--text-secondary)]">
        <Link to={`/projects/${project.id}/chat`} className="hover:text-[var(--brand)]">
          {project.name}
        </Link>
      </p>
      <h1 className="mt-1 text-[22px] font-semibold tracking-tight">Drafts</h1>
      <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
        Versioned scripts from agent runs. Chat stays one thread — each Generate adds a draft.
      </p>

      {drafts.length === 0 ? (
        <div className="mt-10 rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-0)] p-8 text-center">
          <p className="text-[14px] font-medium">No drafts yet</p>
          <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
            {listError || 'Generate a script in chat — each run becomes a versioned draft.'}
          </p>
          <Link
            to={`/projects/${project.id}/chat`}
            className="mt-3 inline-block text-[13px] font-medium text-[var(--brand)] hover:underline"
          >
            Generate in chat
          </Link>
        </div>
      ) : (
        <div className="mt-6 grid gap-4 lg:grid-cols-[240px_minmax(0,1fr)]">
          <aside className="space-y-1">
            {drafts.map((d) => {
              const active = selected?.id === d.id
              return (
                <button
                  key={d.id}
                  type="button"
                  onClick={() => void selectDraft(d.id)}
                  className={`w-full rounded-[8px] border px-3 py-2.5 text-left transition-colors ${
                    active
                      ? 'border-[var(--brand)]/30 bg-[var(--surface-1)]'
                      : 'border-[var(--folio-border)] hover:bg-[var(--surface-1)]'
                  }`}
                >
                  <p className="text-[13px] font-semibold">
                    v{d.version}
                    {d.title ? ` · ${d.title}` : ''}
                  </p>
                  {d.prompt_snippet ? (
                    <p className="mt-1 line-clamp-2 text-[11px] text-[var(--text-secondary)]">
                      {d.prompt_snippet}
                    </p>
                  ) : null}
                  <p className="mt-1.5 text-[10px] text-[var(--text-muted)]">
                    {formatDate(d.created_at)}
                  </p>
                </button>
              )
            })}
          </aside>

          <section className="rounded-[10px] border border-[var(--folio-border)] p-5">
            {detailLoading ? (
              <div className="flex min-h-[240px] items-center justify-center">
                <KissaLoader size="sm" label="Opening draft…" />
              </div>
            ) : selected ? (
              <>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-[14px] font-semibold">
                      Version {selected.version}
                      {(selected.package as { title?: string })?.title
                        ? ` · ${(selected.package as { title?: string }).title}`
                        : ''}
                    </h2>
                    <p className="mt-0.5 text-[12px] text-[var(--text-secondary)]">
                      Run {selected.run_id.slice(0, 8)}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Link
                      to={`/projects/${project.id}/chat`}
                      className="inline-flex h-8 items-center rounded-[6px] bg-[var(--surface-1)] px-3 text-[12px] font-medium text-[var(--text-primary)] hover:bg-[var(--surface-0)]"
                    >
                      View in chat
                    </Link>
                    <Link
                      to={`/editor?project=${project.id}&draft=${selected.id}`}
                      className="inline-flex h-8 items-center rounded-[6px] bg-[var(--brand)] px-3 text-[12px] font-medium text-white"
                    >
                      Open in Editor
                    </Link>
                  </div>
                </div>
                <pre className="mt-4 max-h-[60vh] overflow-auto font-sans text-[13px] leading-relaxed whitespace-pre-wrap">
                  {selected.screenplay_md}
                </pre>
              </>
            ) : (
              <p className="text-[13px] text-[var(--text-secondary)]">Select a draft</p>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
