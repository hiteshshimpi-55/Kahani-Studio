import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { KissaLoader } from '@/components/ui/kissa-loader'
import { Button } from '@/components/ui/button'
import {
  TimelineEditor,
  buildTimelineFromScript,
  clearTimeline,
  loadTimeline,
  saveTimeline,
  type TimelineDoc,
} from '@/features/editor/timeline'
import { getScript, listProjects, listScripts } from '@/features/projects/api/projects-api'
import type { Project, ScriptLatest, ScriptSummary } from '@/features/projects/types'
import { NotFoundView } from '@/features/system/pages/NotFoundPage'

type RecentDraft = ScriptSummary & { project_name: string }

export function EditorPage() {
  const [params] = useSearchParams()
  const projectId = params.get('project')
  const draftId = params.get('draft')

  const [loading, setLoading] = useState(true)
  const [script, setScript] = useState<ScriptLatest | null>(null)
  const [recent, setRecent] = useState<RecentDraft[]>([])
  const [error, setError] = useState<string | null>(null)
  const [timeline, setTimeline] = useState<TimelineDoc | null>(null)

  useEffect(() => {
    void (async () => {
      setLoading(true)
      setError(null)
      try {
        if (projectId && draftId) {
          const s = await getScript(projectId, draftId)
          setScript(s)
          setRecent([])
          const stored = loadTimeline(projectId, draftId)
          if (stored) {
            setTimeline(stored)
          } else {
            const seeded = buildTimelineFromScript(s.package)
            setTimeline(seeded)
            saveTimeline(projectId, draftId, seeded)
          }
        } else {
          setScript(null)
          setTimeline(null)
          const projects: Project[] = await listProjects()
          const collected: RecentDraft[] = []
          for (const p of projects.slice(0, 8)) {
            try {
              const scripts = await listScripts(p.id)
              for (const s of scripts.slice(0, 3)) {
                collected.push({ ...s, project_name: p.name })
              }
            } catch {
              /* no scripts */
            }
          }
          collected.sort(
            (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
          )
          setRecent(collected.slice(0, 12))
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load editor')
      } finally {
        setLoading(false)
      }
    })()
  }, [projectId, draftId])

  const updateTimeline = (doc: TimelineDoc) => {
    setTimeline(doc)
    if (projectId && draftId) saveTimeline(projectId, draftId, doc)
  }

  const reseeds = () => {
    if (!script || !projectId || !draftId) return
    clearTimeline(projectId, draftId)
    const seeded = buildTimelineFromScript(script.package)
    updateTimeline(seeded)
  }

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <KissaLoader label="Opening editor…" />
      </div>
    )
  }

  if (error) {
    return (
      <NotFoundView
        kind={projectId && draftId ? 'draft' : 'resource'}
        detail={error}
      />
    )
  }

  if (projectId && draftId && !script && !loading) {
    return <NotFoundView kind="draft" />
  }

  if (script && projectId && draftId && timeline) {
    const title =
      typeof script.package?.title === 'string' ? script.package.title : `Draft v${script.version}`
    return (
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-[12px] text-[var(--text-secondary)]">Editor · multi-track</p>
            <h1 className="mt-1 text-[22px] font-semibold tracking-tight">{title}</h1>
            <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
              One lane per voice · separate Music & SFX ·{' '}
              <Link
                to={`/projects/${projectId}/drafts?draft=${script.id}`}
                className="text-[var(--brand)] hover:underline"
              >
                Back to drafts
              </Link>
            </p>
          </div>
          <Button type="button" size="sm" variant="secondary" onClick={reseeds}>
            Reseed from script
          </Button>
        </div>

        <div className="mt-6">
          <TimelineEditor
            projectId={projectId}
            doc={timeline}
            onChange={updateTimeline}
            scriptPreview={script.screenplay_md}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-[22px] font-semibold tracking-tight">Editor</h1>
      <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
        Open a draft from a project, or pick a recent script below.
      </p>

      {recent.length === 0 ? (
        <div className="mt-10 rounded-[10px] border border-dashed border-[var(--folio-border)] p-8 text-center">
          <p className="text-[14px] font-medium">No drafts yet</p>
          <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
            Generate a script in project chat, then open it here.
          </p>
          <Link to="/" className="mt-3 inline-block text-[13px] font-medium text-[var(--brand)]">
            Go to projects
          </Link>
        </div>
      ) : (
        <div className="mt-6 space-y-2">
          {recent.map((d) => (
            <Link
              key={d.id}
              to={`/editor?project=${d.project_id}&draft=${d.id}`}
              className="block rounded-[10px] border border-[var(--folio-border)] px-4 py-3 transition-colors hover:bg-[var(--surface-1)]"
            >
              <p className="text-[13px] font-semibold">
                {d.project_name} · v{d.version}
                {d.title ? ` · ${d.title}` : ''}
              </p>
              {d.prompt_snippet ? (
                <p className="mt-1 line-clamp-1 text-[12px] text-[var(--text-secondary)]">
                  {d.prompt_snippet}
                </p>
              ) : null}
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
