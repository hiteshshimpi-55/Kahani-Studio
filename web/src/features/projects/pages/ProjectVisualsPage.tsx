import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { LoaderCircle } from 'lucide-react'

import { KissaLoader } from '@/components/ui/kissa-loader'
import * as projectsApi from '@/features/projects/api/projects-api'
import { useProject } from '@/features/projects/hooks/use-project'
import type { ProjectRun, VisualEpisodeStatus } from '@/features/projects/types'
import { NotFoundView } from '@/features/system/pages/NotFoundPage'

function pickVisualRun(runs: ProjectRun[]): ProjectRun | null {
  const withVisuals = runs.find((r) => {
    const v = r.stage_statuses?.visuals
    return v === 'generating' || v === 'approved' || v === 'failed'
  })
  if (withVisuals) return withVisuals
  return (
    runs.find((r) => Boolean(r.artifacts?.audio_url || r.artifacts?.audio_key)) ||
    runs[0] ||
    null
  )
}

export function ProjectVisualsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { project, loading, error } = useProject(projectId)
  const [run, setRun] = useState<ProjectRun | null>(null)
  const [visuals, setVisuals] = useState<VisualEpisodeStatus | null>(null)
  const [busy, setBusy] = useState(false)
  const [pageError, setPageError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!projectId) return
    setPageError(null)
    try {
      const runs = await projectsApi.listRuns(projectId)
      const sorted = [...runs].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      )
      const chosen = pickVisualRun(sorted)
      setRun(chosen)
      const seriesId = chosen?.artifacts?.visuals_series_id || chosen?.id
      if (!seriesId) {
        setVisuals(null)
        return
      }
      try {
        setVisuals(await projectsApi.getVisualEpisode(seriesId))
      } catch {
        setVisuals(null)
      }
    } catch (e) {
      setPageError(e instanceof Error ? e.message : 'Failed to load visuals')
    }
  }, [projectId])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    if (run?.stage_statuses?.visuals !== 'generating') return
    const id = window.setInterval(() => {
      void load()
    }, 4000)
    return () => window.clearInterval(id)
  }, [run?.stage_statuses?.visuals, load])

  const startVisuals = async () => {
    if (!projectId || !run) return
    setBusy(true)
    setPageError(null)
    try {
      const next = await projectsApi.startRunVisuals(projectId, run.id)
      setRun(next)
      await load()
    } catch (e) {
      setPageError(e instanceof Error ? e.message : 'Could not start visuals')
    } finally {
      setBusy(false)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <KissaLoader label="Loading visuals…" />
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

  const visualsStatus = run?.stage_statuses?.visuals || 'idle'
  const lookbookEntries = Object.entries(visuals?.lookbook || {}).filter(([, url]) => Boolean(url))
  const stillEntries = Object.entries(visuals?.stills || {}).filter(([, url]) => Boolean(url))
  const canStart =
    Boolean(run?.artifacts?.audio_url || run?.artifacts?.audio_key) &&
    (visualsStatus === 'idle' || visualsStatus === 'failed' || visualsStatus === 'rejected')

  return (
    <div className="mx-auto max-w-4xl">
      <p className="text-[12px] text-[var(--text-secondary)]">
        <Link to={`/projects/${project.id}/chat`} className="hover:text-[var(--brand)]">
          {project.name}
        </Link>
      </p>
      <h1 className="mt-1 text-[22px] font-semibold tracking-tight">Visuals</h1>
      <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
        Character lookbook and scene stills timed to the episode audio — reference frames for the
        companion visual track.
      </p>

      {pageError ? <p className="mt-4 text-[13px] text-destructive">{pageError}</p> : null}

      {!run ? (
        <div className="mt-10 rounded-[10px] border border-dashed border-[var(--folio-border)] bg-[var(--surface-0)] p-10 text-center">
          <p className="text-[14px] font-medium">No episode run yet</p>
          <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
            Generate a script and audio in chat first, then create companion visuals.
          </p>
          <Link
            to={`/projects/${project.id}/chat`}
            className="mt-3 inline-block text-[13px] font-medium text-[var(--brand)] hover:underline"
          >
            Open chat
          </Link>
        </div>
      ) : (
        <div className="mt-6 space-y-8">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-[13px] text-[var(--text-secondary)]">
              Run <span className="font-mono text-[12px]">{run.id.slice(0, 8)}</span>
              {visualsStatus !== 'idle' ? ` · ${visualsStatus}` : ''}
              {visuals?.shot_count != null ? ` · ${visuals.shot_count} stills` : ''}
            </p>
            {canStart ? (
              <button
                type="button"
                disabled={busy}
                onClick={() => void startVisuals()}
                className="rounded-[8px] bg-[var(--brand)] px-3 py-1.5 text-[12px] font-medium text-white disabled:opacity-50"
              >
                {busy ? 'Starting…' : visualsStatus === 'failed' ? 'Retry visuals' : 'Generate visuals'}
              </button>
            ) : null}
            {visualsStatus === 'generating' ? (
              <p className="flex items-center gap-2 text-[13px] text-[var(--text-secondary)]">
                <LoaderCircle className="h-3.5 w-3.5 animate-spin text-[var(--brand)]" />
                Building lookbook and scene stills…
              </p>
            ) : null}
          </div>

          {lookbookEntries.length > 0 ? (
            <section>
              <h2 className="text-[11px] font-semibold tracking-[0.14em] text-[var(--text-muted)] uppercase">
                Lookbook
              </h2>
              <ul className="mt-3 flex flex-wrap gap-4">
                {lookbookEntries.map(([key, url]) => (
                  <li key={key} className="w-[120px]">
                    <img
                      src={url}
                      alt={key}
                      className="aspect-[3/4] w-full rounded-[10px] object-cover ring-1 ring-[var(--folio-border)]"
                    />
                    <p className="mt-1.5 truncate text-[12px] text-[var(--text-secondary)]">
                      {key.replace(/\.png$/i, '')}
                    </p>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {stillEntries.length > 0 ? (
            <section>
              <h2 className="text-[11px] font-semibold tracking-[0.14em] text-[var(--text-muted)] uppercase">
                Scene stills
              </h2>
              <ul className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
                {stillEntries.map(([key, url]) => (
                  <li key={key}>
                    <img
                      src={url}
                      alt={key}
                      className="aspect-[9/16] w-full rounded-[10px] object-cover ring-1 ring-[var(--folio-border)]"
                    />
                    <p className="mt-1 truncate text-[11px] text-[var(--text-muted)]">{key}</p>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {visuals?.video_url ? (
            <section>
              <h2 className="text-[11px] font-semibold tracking-[0.14em] text-[var(--text-muted)] uppercase">
                Episode video
              </h2>
              <video
                controls
                className="mt-3 max-h-[480px] w-full max-w-[280px] rounded-[12px] ring-1 ring-[var(--folio-border)]"
                src={visuals.video_url}
                preload="metadata"
              >
                <track kind="captions" />
              </video>
            </section>
          ) : null}

          {!lookbookEntries.length && !stillEntries.length && visualsStatus !== 'generating' ? (
            <div className="rounded-[10px] border border-dashed border-[var(--folio-border)] bg-[var(--surface-0)] p-8 text-center">
              <p className="text-[14px] font-medium">No visuals yet</p>
              <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
                After audio is ready in chat, choose Generate visuals — or start them here.
              </p>
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}
