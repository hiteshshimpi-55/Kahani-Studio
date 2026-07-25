import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown, ChevronRight, LoaderCircle } from 'lucide-react'

import { apiUrl } from '@/lib/api-client'
import * as projectsApi from '@/features/projects/api/projects-api'
import type { ProjectRun, StageStatus, VisualEpisodeStatus } from '@/features/projects/types'

import { ApprovalPanel } from './ApprovalPanel'
import { PipelineStepper } from './PipelineStepper'

type CastMember = {
  id?: string
  name?: string
  role?: string
  voice?: string
}

function activeApprovalStage(
  statuses?: ProjectRun['stage_statuses'],
): 'script' | 'audio' | 'cover_art' | null {
  if (!statuses) return 'script'
  if (statuses.script === 'pending_approval' || statuses.script === 'failed') return 'script'
  if (statuses.audio === 'pending_approval' || statuses.audio === 'failed') return 'audio'
  if (statuses.cover_art === 'pending_approval' || statuses.cover_art === 'failed') {
    return 'cover_art'
  }
  return null
}

function stageLabel(stage: string): string {
  if (stage === 'cover_art') return 'Cover'
  if (stage === 'assembly') return 'Assembly'
  return stage.charAt(0).toUpperCase() + stage.slice(1)
}

export function ProductionCard({
  projectId,
  scriptId,
  runId,
  preview,
  package: scriptPackage,
  isDraft,
  onSaveDraft,
  onUpdateDraft,
  onContinue,
}: {
  projectId: string
  scriptId?: string
  runId?: string
  preview: string
  package?: {
    title?: string
    bible?: { characters?: CastMember[] }
    parts?: Array<{ part_number?: number; title?: string; cliff_out?: string }>
  } | null
  isDraft?: boolean
  onSaveDraft?: (text?: string) => void | Promise<{ id: string } | void>
  onUpdateDraft?: (text: string) => void | Promise<void>
  onContinue?: () => void
}) {
  const [run, setRun] = useState<ProjectRun | null>(null)
  const [editing, setEditing] = useState(false)
  const [draftText, setDraftText] = useState(preview)
  const [busy, setBusy] = useState(false)
  const [actionBusy, setActionBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [scriptOpen, setScriptOpen] = useState(true)
  const [localScriptId, setLocalScriptId] = useState<string | undefined>(scriptId)
  const [visuals, setVisuals] = useState<VisualEpisodeStatus | null>(null)
  const pollRef = useRef<number | null>(null)
  const visualsPollRef = useRef<number | null>(null)

  const refreshRun = useCallback(async () => {
    if (!runId) return null
    const next = await projectsApi.getRun(projectId, runId)
    setRun(next)
    if (next.draft_script_id) setLocalScriptId(next.draft_script_id)
    if (next.screenplay_md) setDraftText(next.screenplay_md)
    return next
  }, [projectId, runId])

  useEffect(() => {
    if (scriptId) setLocalScriptId(scriptId)
  }, [scriptId])

  useEffect(() => {
    if (!editing) setDraftText(preview)
  }, [preview, editing])

  useEffect(() => {
    if (!runId) return
    let cancelled = false
    void (async () => {
      try {
        const next = await refreshRun()
        if (cancelled || !next) return
        const statuses = next.stage_statuses || {}
        const generating = Object.values(statuses).some((s) => s === 'generating')
        const incomplete = next.current_stage !== 'complete'
        if (generating || incomplete) {
          if (pollRef.current) window.clearInterval(pollRef.current)
          pollRef.current = window.setInterval(() => {
            void refreshRun().then((latest) => {
              if (!latest) return
              const st = latest.stage_statuses || {}
              const stillGenerating = Object.values(st).some((s) => s === 'generating')
              if (latest.current_stage === 'complete' && !stillGenerating) {
                if (pollRef.current) window.clearInterval(pollRef.current)
                pollRef.current = null
              }
            })
          }, 2500)
        }
      } catch {
        /* ignore */
      }
    })()
    return () => {
      cancelled = true
      if (pollRef.current) window.clearInterval(pollRef.current)
    }
  }, [runId, refreshRun])

  const seriesId =
    run?.artifacts?.visuals_series_id || runId || undefined

  const refreshVisuals = useCallback(async () => {
    if (!seriesId) return null
    try {
      const next = await projectsApi.getVisualEpisode(seriesId)
      setVisuals(next)
      return next
    } catch {
      return null
    }
  }, [seriesId])

  useEffect(() => {
    const vs = run?.stage_statuses?.visuals
    if (!seriesId || !vs || vs === 'idle' || vs === 'rejected') {
      if (visualsPollRef.current) {
        window.clearInterval(visualsPollRef.current)
        visualsPollRef.current = null
      }
      return
    }
    void refreshVisuals()
    if (vs === 'generating' || vs === 'approved') {
      if (visualsPollRef.current) window.clearInterval(visualsPollRef.current)
      visualsPollRef.current = window.setInterval(() => {
        void refreshVisuals().then((latest) => {
          if (!latest) return
          if (latest.status === 'ready' || (latest.stills && Object.keys(latest.stills).length > 0)) {
            if (visualsPollRef.current) {
              window.clearInterval(visualsPollRef.current)
              visualsPollRef.current = null
            }
          }
        })
      }, 4000)
    }
    return () => {
      if (visualsPollRef.current) {
        window.clearInterval(visualsPollRef.current)
        visualsPollRef.current = null
      }
    }
  }, [run?.stage_statuses?.visuals, seriesId, refreshVisuals])

  const statuses = run?.stage_statuses || {
    script: preview ? 'pending_approval' : 'idle',
    audio: 'idle',
    cover_art: 'idle',
    assembly: 'idle',
  }
  const currentStage = run?.current_stage || 'script'
  const approvalStage = activeApprovalStage(statuses)
  const coverUrl = run?.artifacts?.cover_url ? apiUrl(run.artifacts.cover_url) : null
  const audioUrl = run?.artifacts?.audio_url ? apiUrl(run.artifacts.audio_url) : null
  const cast = scriptPackage?.bible?.characters ?? []
  const part = scriptPackage?.parts?.[0]
  const partLabel =
    part?.part_number != null
      ? `Episode ${part.part_number}${part.title ? `: ${part.title}` : ''}`
      : scriptPackage?.title || 'Episode output'

  const screenplay = run?.screenplay_md || draftText || preview

  const handleApprove = async (stage: string) => {
    if (!runId) return
    setActionBusy(true)
    setError(null)
    try {
      // Auto-save draft when approving script so cast/continuity lock in
      if (stage === 'script' && onSaveDraft && !localScriptId) {
        setBusy(true)
        try {
          const saved = await onSaveDraft(editing ? draftText : undefined)
          setEditing(false)
          if (saved && typeof saved === 'object' && 'id' in saved) {
            setLocalScriptId(saved.id)
          }
        } finally {
          setBusy(false)
        }
      }
      const next = await projectsApi.approveStage(projectId, runId, stage)
      setRun(next)
      setScriptOpen(stage !== 'script')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Approve failed')
    } finally {
      setActionBusy(false)
    }
  }

  const handleReject = async (
    stage: string,
    action: 'regenerate' | 'revise',
    notes?: string,
  ) => {
    if (!runId) return
    setActionBusy(true)
    setError(null)
    try {
      const next = await projectsApi.rejectStage(projectId, runId, stage, {
        action,
        notes,
      })
      setRun(next)
      if (stage === 'script') setScriptOpen(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Reject failed')
    } finally {
      setActionBusy(false)
    }
  }

  const handleStartVisuals = async () => {
    if (!runId) return
    setActionBusy(true)
    setError(null)
    try {
      const next = await projectsApi.startRunVisuals(projectId, runId)
      setRun(next)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not start visuals')
    } finally {
      setActionBusy(false)
    }
  }

  const handleSkipVisuals = async () => {
    if (!runId) return
    setActionBusy(true)
    setError(null)
    try {
      const next = await projectsApi.skipRunVisuals(projectId, runId)
      setRun(next)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not skip visuals')
    } finally {
      setActionBusy(false)
    }
  }

  const editorHref = localScriptId
    ? `/editor?project=${projectId}&draft=${localScriptId}`
    : `/projects/${projectId}/drafts`

  const assemblyDone = currentStage === 'complete' || statuses.assembly === 'approved'
  const audioGenerating = statuses.audio === 'generating'
  const coverGenerating = statuses.cover_art === 'generating'
  const assemblyGenerating = statuses.assembly === 'generating'
  const visualsStatus = (statuses.visuals as StageStatus | string | undefined) || 'idle'
  const audioReady =
    Boolean(audioUrl) &&
    (statuses.audio === 'pending_approval' ||
      statuses.audio === 'approved' ||
      statuses.audio === 'failed')
  const askVisuals = audioReady && (visualsStatus === 'idle' || visualsStatus === 'failed')
  const visualsGenerating = visualsStatus === 'generating'
  const lookbookEntries = Object.entries(visuals?.lookbook || {}).filter(([, url]) => Boolean(url))
  const stillEntries = Object.entries(visuals?.stills || {}).filter(([, url]) => Boolean(url))
  const hasVisualAssets = lookbookEntries.length > 0 || stillEntries.length > 0

  return (
    <article className="chat-tool-enter my-3 overflow-hidden rounded-[16px] border border-[var(--folio-border-strong)] bg-[var(--surface-2)] shadow-[var(--shadow-card)]">
      <div className="flex flex-wrap items-start gap-4 border-b border-[var(--folio-border)] px-4 py-3">
        {coverUrl ? (
          <img
            src={coverUrl}
            alt="Episode cover"
            className="h-28 w-[78px] shrink-0 rounded-[10px] object-cover ring-1 ring-[var(--folio-border)]"
          />
        ) : coverGenerating ? (
          <div className="flex h-28 w-[78px] shrink-0 items-center justify-center rounded-[10px] bg-[var(--surface-1)] text-[var(--text-muted)]">
            <LoaderCircle className="h-5 w-5 animate-spin text-[var(--brand)]" />
          </div>
        ) : null}
        <div className="min-w-0 flex-1 space-y-2">
          <p className="text-[11px] font-semibold tracking-[0.14em] text-[var(--text-muted)] uppercase">
            {partLabel}
          </p>
          <PipelineStepper stageStatuses={statuses} currentStage={currentStage} />
          {assemblyDone ? (
            <p className="text-[13px] font-medium text-emerald-700">
              Episode package ready — script, audio, and cover approved.
            </p>
          ) : null}
        </div>
      </div>

      {cast.length > 0 ? (
        <div className="border-b border-[var(--folio-border)] px-4 py-3">
          <p className="mb-2 text-[11px] font-semibold tracking-[0.12em] text-[var(--text-muted)] uppercase">
            Cast
          </p>
          <ul className="flex flex-wrap gap-2">
            {cast.map((ch, i) => (
              <li
                key={ch.id || ch.name || i}
                className="max-w-full rounded-[8px] bg-[var(--surface-1)] px-2.5 py-1.5"
                title={ch.voice || undefined}
              >
                <span className="text-[12px] font-medium text-[var(--text-primary)]">
                  {ch.name || ch.id || 'Character'}
                </span>
                {ch.role ? (
                  <span className="ml-1.5 text-[11px] text-[var(--text-secondary)]">{ch.role}</span>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {/* Script preview */}
      <div className="border-b border-[var(--folio-border)] px-4 py-3">
        <button
          type="button"
          className="mb-2 flex items-center gap-1 text-[12px] font-medium text-[var(--text-secondary)] hover:text-[var(--brand)]"
          onClick={() => setScriptOpen((v) => !v)}
        >
          {scriptOpen ? (
            <ChevronDown className="h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" />
          )}
          {scriptOpen ? 'Hide script' : 'View script'}
          {statuses.script === 'approved' ? ' (approved)' : ''}
        </button>
        {scriptOpen ? (
          editing ? (
            <div>
              <textarea
                value={draftText}
                onChange={(e) => setDraftText(e.target.value)}
                rows={12}
                className="w-full resize-y rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-0)] px-3 py-2 font-sans text-[13px] leading-6 text-[var(--text-primary)] outline-none focus:ring-2 focus:ring-[var(--brand)]/30"
              />
              {(isDraft || localScriptId) && onUpdateDraft ? (
                <div className="mt-3 flex justify-end gap-2">
                  <button
                    type="button"
                    disabled={busy || !draftText.trim()}
                    className="rounded-[8px] bg-[var(--brand)] px-3 py-1.5 text-[12px] font-medium text-white disabled:opacity-50"
                    onClick={() => {
                      void (async () => {
                        setBusy(true)
                        try {
                          await onUpdateDraft(draftText)
                          setEditing(false)
                        } finally {
                          setBusy(false)
                        }
                      })()
                    }}
                  >
                    {busy ? 'Saving…' : 'Save changes'}
                  </button>
                </div>
              ) : null}
            </div>
          ) : (
            <pre className="max-h-[240px] overflow-y-auto font-sans text-[13px] leading-6 whitespace-pre-wrap text-[var(--text-primary)]">
              {screenplay}
            </pre>
          )
        ) : null}
        {statuses.script === 'pending_approval' || statuses.script === 'failed' ? (
          <div className="mt-3">
            <ApprovalPanel
              stageLabel="Script"
              status={statuses.script as StageStatus}
              busy={actionBusy || busy}
              onApprove={() => handleApprove('script')}
              onRegenerate={() => handleReject('script', 'regenerate')}
              onRevise={(notes) => handleReject('script', 'revise', notes)}
            />
          </div>
        ) : null}
      </div>

      {/* Audio stage */}
      {(audioUrl || audioGenerating || approvalStage === 'audio' || statuses.audio === 'approved') && (
        <div className="border-b border-[var(--folio-border)] px-4 py-3 space-y-3">
          <p className="text-[11px] font-semibold tracking-[0.14em] text-[var(--text-muted)] uppercase">
            Audio
            {run?.progress?.total_lines ? ` · ${run.progress.total_lines} lines` : ''}
            {run?.progress?.duration_sec
              ? ` · ${Math.round(run.progress.duration_sec)}s`
              : ''}
          </p>
          {audioGenerating ? (
            <p className="flex items-center gap-2 text-[13px] text-[var(--text-secondary)]">
              <LoaderCircle className="h-3.5 w-3.5 animate-spin text-[var(--brand)]" />
              Casting voices and rendering audio…
            </p>
          ) : null}
          {audioUrl ? (
            <audio controls className="w-full" src={audioUrl} preload="metadata">
              <track kind="captions" />
            </audio>
          ) : null}
          {approvalStage === 'audio' || statuses.audio === 'failed' ? (
            <ApprovalPanel
              stageLabel="Audio"
              status={statuses.audio as StageStatus}
              busy={actionBusy}
              onApprove={() => handleApprove('audio')}
              onRegenerate={() => handleReject('audio', 'regenerate')}
              onRevise={(notes) => handleReject('audio', 'revise', notes)}
            />
          ) : statuses.audio === 'approved' ? (
            <p className="text-[12px] text-[var(--text-secondary)]">Audio approved</p>
          ) : null}
        </div>
      )}

      {/* Companion visuals (optional, after audio) */}
      {(askVisuals ||
        visualsGenerating ||
        visualsStatus === 'approved' ||
        hasVisualAssets) && (
        <div className="border-b border-[var(--folio-border)] px-4 py-3 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-[11px] font-semibold tracking-[0.14em] text-[var(--text-muted)] uppercase">
              Companion visuals
            </p>
            {hasVisualAssets ? (
              <Link
                to={`/projects/${projectId}/visuals`}
                className="text-[12px] font-medium text-[var(--brand)] hover:underline"
              >
                Open visuals page
              </Link>
            ) : null}
          </div>

          {askVisuals ? (
            <div className="rounded-[12px] bg-[var(--surface-1)] px-3 py-3">
              <p className="text-[13px] font-medium text-[var(--text-primary)]">
                Create companion visuals for this episode?
              </p>
              <p className="mt-1 text-[12px] text-[var(--text-secondary)]">
                We&apos;ll build a character lookbook, then scene stills timed to the audio for
                reference.
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={actionBusy}
                  onClick={() => void handleStartVisuals()}
                  className="rounded-[8px] bg-[var(--brand)] px-3 py-1.5 text-[12px] font-medium text-white disabled:opacity-50"
                >
                  {visualsStatus === 'failed' ? 'Retry visuals' : 'Generate visuals'}
                </button>
                {visualsStatus === 'idle' ? (
                  <button
                    type="button"
                    disabled={actionBusy}
                    onClick={() => void handleSkipVisuals()}
                    className="rounded-[8px] px-3 py-1.5 text-[12px] font-medium text-[var(--text-secondary)] hover:bg-[var(--surface-0)] disabled:opacity-50"
                  >
                    Skip
                  </button>
                ) : null}
              </div>
            </div>
          ) : null}

          {visualsGenerating ? (
            <p className="flex items-center gap-2 text-[13px] text-[var(--text-secondary)]">
              <LoaderCircle className="h-3.5 w-3.5 animate-spin text-[var(--brand)]" />
              Creating lookbook, then scene stills…
            </p>
          ) : null}

          {lookbookEntries.length > 0 ? (
            <div>
              <p className="mb-2 text-[11px] font-semibold tracking-[0.12em] text-[var(--text-muted)] uppercase">
                Lookbook
              </p>
              <ul className="flex flex-wrap gap-3">
                {lookbookEntries.map(([key, url]) => (
                  <li key={key} className="w-[88px]">
                    <img
                      src={url}
                      alt={key}
                      className="aspect-[3/4] w-full rounded-[8px] object-cover ring-1 ring-[var(--folio-border)]"
                    />
                    <p className="mt-1 truncate text-[11px] text-[var(--text-secondary)]">
                      {key.replace(/\.png$/i, '')}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {stillEntries.length > 0 ? (
            <div>
              <p className="mb-2 text-[11px] font-semibold tracking-[0.12em] text-[var(--text-muted)] uppercase">
                Scene stills
              </p>
              <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {stillEntries.slice(0, 9).map(([key, url]) => (
                  <li key={key}>
                    <img
                      src={url}
                      alt={key}
                      className="aspect-[9/16] w-full rounded-[8px] object-cover ring-1 ring-[var(--folio-border)]"
                    />
                  </li>
                ))}
              </ul>
              {stillEntries.length > 9 ? (
                <p className="mt-2 text-[12px] text-[var(--text-secondary)]">
                  +{stillEntries.length - 9} more on the visuals page
                </p>
              ) : null}
            </div>
          ) : null}

          {visuals?.video_url ? (
            <video
              controls
              className="mx-auto max-h-80 w-full max-w-[220px] rounded-[12px] ring-1 ring-[var(--folio-border)]"
              src={visuals.video_url}
              preload="metadata"
            >
              <track kind="captions" />
            </video>
          ) : null}
        </div>
      )}

      {/* Cover stage */}
      {(coverUrl ||
        coverGenerating ||
        approvalStage === 'cover_art' ||
        statuses.cover_art === 'approved') && (
        <div className="border-b border-[var(--folio-border)] px-4 py-3 space-y-3">
          <p className="text-[11px] font-semibold tracking-[0.14em] text-[var(--text-muted)] uppercase">
            Cover art
          </p>
          {coverGenerating ? (
            <p className="flex items-center gap-2 text-[13px] text-[var(--text-secondary)]">
              <LoaderCircle className="h-3.5 w-3.5 animate-spin text-[var(--brand)]" />
              Generating cover from script and audio mood…
            </p>
          ) : null}
          {coverUrl ? (
            <img
              src={coverUrl}
              alt="Cover preview"
              className="mx-auto max-h-64 rounded-[12px] object-contain ring-1 ring-[var(--folio-border)]"
            />
          ) : null}
          {approvalStage === 'cover_art' || statuses.cover_art === 'failed' ? (
            <ApprovalPanel
              stageLabel="Cover"
              status={statuses.cover_art as StageStatus}
              busy={actionBusy}
              onApprove={() => handleApprove('cover_art')}
              onRegenerate={() => handleReject('cover_art', 'regenerate')}
              onRevise={(notes) => handleReject('cover_art', 'revise', notes)}
            />
          ) : statuses.cover_art === 'approved' ? (
            <p className="text-[12px] text-[var(--text-secondary)]">Cover approved</p>
          ) : null}
        </div>
      )}

      {assemblyGenerating ? (
        <div className="border-b border-[var(--folio-border)] px-4 py-3">
          <p className="flex items-center gap-2 text-[13px] text-[var(--text-secondary)]">
            <LoaderCircle className="h-3.5 w-3.5 animate-spin text-[var(--brand)]" />
            Assembling final episode package…
          </p>
        </div>
      ) : null}

      {error || run?.error ? (
        <div className="border-b border-[var(--folio-border)] px-4 py-2">
          <p className="text-[12px] text-destructive">{error || run?.error}</p>
        </div>
      ) : null}

      <div className="flex flex-wrap items-center gap-3 px-4 py-3">
        {(isDraft || localScriptId ? onUpdateDraft : onSaveDraft) &&
        statuses.script === 'pending_approval' ? (
          <button
            type="button"
            className="text-[12px] font-medium text-[var(--text-secondary)] hover:text-[var(--brand)]"
            onClick={() => {
              setDraftText(screenplay)
              setEditing((v) => !v)
            }}
          >
            {editing ? 'Cancel edit' : 'Edit script'}
          </button>
        ) : null}
        {(isDraft || localScriptId) && localScriptId ? (
          <Link
            to={editorHref}
            className="text-[12px] font-medium text-[var(--brand)] hover:underline"
          >
            Open in Editor
          </Link>
        ) : null}
        {onContinue && assemblyDone ? (
          <button
            type="button"
            className="text-[13px] font-medium text-[var(--brand)] hover:underline"
            onClick={onContinue}
          >
            Continue to next episode
          </button>
        ) : null}
        {currentStage && currentStage !== 'complete' && approvalStage ? (
          <span className="ml-auto text-[11px] text-[var(--text-muted)]">
            Awaiting {stageLabel(approvalStage)} approval
          </span>
        ) : null}
      </div>
    </article>
  )
}
