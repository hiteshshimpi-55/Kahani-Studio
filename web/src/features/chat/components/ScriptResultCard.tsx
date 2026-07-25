import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { LoaderCircle, Volume2 } from 'lucide-react'

import { apiUrl } from '@/lib/api-client'
import * as projectsApi from '@/features/projects/api/projects-api'
import type { ScriptAudioStatus } from '@/features/projects/api/projects-api'

export function ScriptResultCard({
  projectId,
  scriptId,
  runId,
  preview,
  isDraft,
  onSaveDraft,
  onUpdateDraft,
}: {
  projectId: string
  scriptId?: string
  runId?: string
  preview: string
  isDraft?: boolean
  onSaveDraft?: (text?: string) => void | Promise<{ id: string } | void>
  onUpdateDraft?: (text: string) => void | Promise<void>
}) {
  const [editing, setEditing] = useState(false)
  const [draftText, setDraftText] = useState(preview)
  const [busy, setBusy] = useState(false)
  const [audioBusy, setAudioBusy] = useState(false)
  const [localScriptId, setLocalScriptId] = useState<string | undefined>(scriptId)
  const [audioStatus, setAudioStatus] = useState<ScriptAudioStatus | null>(null)
  const [audioError, setAudioError] = useState<string | null>(null)
  const pollRef = useRef<number | null>(null)

  useEffect(() => {
    if (scriptId) setLocalScriptId(scriptId)
  }, [scriptId])

  useEffect(() => {
    if (!editing) setDraftText(preview)
  }, [preview, editing])

  useEffect(() => {
    if (!localScriptId || !isDraft) return
    let cancelled = false
    void (async () => {
      try {
        const status = await projectsApi.getScriptAudioStatus(projectId, localScriptId)
        if (!cancelled) {
          setAudioStatus(status)
          if (status.status === 'queued' || status.status === 'running') {
            startPoll(localScriptId)
          }
        }
      } catch {
        /* idle is fine */
      }
    })()
    return () => {
      cancelled = true
      if (pollRef.current) window.clearInterval(pollRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, localScriptId, isDraft])

  const startPoll = (id: string) => {
    if (pollRef.current) window.clearInterval(pollRef.current)
    pollRef.current = window.setInterval(async () => {
      try {
        const next = await projectsApi.getScriptAudioStatus(projectId, id)
        setAudioStatus(next)
        if (next.status === 'succeeded' || next.status === 'failed') {
          if (pollRef.current) window.clearInterval(pollRef.current)
          pollRef.current = null
          setAudioBusy(false)
          if (next.status === 'failed') {
            setAudioError(next.error || 'Audio generation failed')
          }
        }
      } catch {
        /* keep polling */
      }
    }, 2500)
  }

  const handleGenerateAudio = async () => {
    setAudioError(null)
    setAudioBusy(true)
    try {
      let id = localScriptId
      if (!id && runId && onSaveDraft) {
        setBusy(true)
        try {
          const saved = await onSaveDraft(editing ? draftText : undefined)
          setEditing(false)
          if (saved && typeof saved === 'object' && 'id' in saved) {
            id = saved.id
            setLocalScriptId(saved.id)
          }
        } finally {
          setBusy(false)
        }
      }
      if (!id) {
        setAudioError('Save as draft first, then generate audio.')
        setAudioBusy(false)
        return
      }
      const status = await projectsApi.generateScriptAudio(projectId, id, {
        max_sec: 300,
        voice_provider: 'elevenlabs',
      })
      setAudioStatus(status)
      if (status.status === 'queued' || status.status === 'running') {
        startPoll(id)
      } else if (status.status === 'succeeded') {
        setAudioBusy(false)
      } else if (status.status === 'failed') {
        setAudioBusy(false)
        setAudioError(status.error || 'Audio generation failed')
      }
    } catch (e) {
      setAudioBusy(false)
      setAudioError(e instanceof Error ? e.message : 'Failed to start audio')
    }
  }

  const draftsHref = localScriptId
    ? `/projects/${projectId}/drafts?draft=${localScriptId}`
    : `/projects/${projectId}/drafts`
  const editorHref = localScriptId
    ? `/editor?project=${projectId}&draft=${localScriptId}`
    : `/projects/${projectId}/drafts`

  const audioSrc =
    audioStatus?.status === 'succeeded' && audioStatus.audio_url
      ? apiUrl(audioStatus.audio_url)
      : null
  const audioInFlight =
    audioBusy || audioStatus?.status === 'queued' || audioStatus?.status === 'running'

  return (
    <article className="chat-tool-enter my-3 overflow-hidden rounded-[16px] border border-[var(--folio-border-strong)] bg-[var(--surface-2)] shadow-[var(--shadow-card)]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--folio-border)] px-4 py-3">
        <p className="text-[11px] font-semibold tracking-[0.14em] text-[var(--text-muted)] uppercase">
          {isDraft || localScriptId ? 'Saved draft' : 'Script output'}
        </p>
        <div className="flex flex-wrap items-center gap-3">
          {!isDraft && !localScriptId && runId && onSaveDraft ? (
            <button
              type="button"
              disabled={busy}
              className="text-[12px] font-medium text-[var(--brand)] hover:underline disabled:opacity-50"
              onClick={() => {
                void (async () => {
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
                })()
              }}
            >
              {busy ? 'Saving…' : 'Add as draft'}
            </button>
          ) : null}
          {(isDraft || localScriptId ? onUpdateDraft : onSaveDraft) ? (
            <button
              type="button"
              className="text-[12px] font-medium text-[var(--text-secondary)] hover:text-[var(--brand)]"
              onClick={() => {
                setDraftText(preview)
                setEditing((v) => !v)
              }}
            >
              {editing ? 'Cancel' : 'Edit'}
            </button>
          ) : null}
          {localScriptId || (runId && onSaveDraft) ? (
            <button
              type="button"
              disabled={audioInFlight || busy}
              className="inline-flex items-center gap-1.5 text-[12px] font-medium text-[var(--brand)] hover:underline disabled:opacity-50"
              onClick={() => void handleGenerateAudio()}
            >
              {audioInFlight ? (
                <>
                  <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                  Generating audio…
                </>
              ) : (
                <>
                  <Volume2 className="h-3.5 w-3.5" />
                  {audioSrc ? 'Regenerate audio' : 'Generate audio'}
                </>
              )}
            </button>
          ) : null}
          {(isDraft || localScriptId) && localScriptId ? (
            <>
              <Link
                to={draftsHref}
                className="text-[12px] font-medium text-[var(--text-secondary)] hover:text-[var(--brand)]"
              >
                Open draft
              </Link>
              <Link
                to={editorHref}
                className="text-[12px] font-medium text-[var(--brand)] hover:underline"
              >
                Open in Editor
              </Link>
            </>
          ) : null}
        </div>
      </div>

      {editing ? (
        <div className="px-4 py-4">
          <textarea
            value={draftText}
            onChange={(e) => setDraftText(e.target.value)}
            rows={14}
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
          ) : (
            <p className="mt-2 text-[11px] text-[var(--text-muted)]">
              Edit freely, then click Add as draft to keep this version.
            </p>
          )}
        </div>
      ) : (
        <pre className="max-h-[280px] overflow-y-auto px-4 py-4 font-sans text-[13px] leading-6 whitespace-pre-wrap text-[var(--text-primary)]">
          {preview}
        </pre>
      )}

      {(audioInFlight || audioSrc || audioError) && (
        <div className="border-t border-[var(--folio-border)] px-4 py-3">
          {audioInFlight ? (
            <p className="flex items-center gap-2 text-[13px] text-[var(--text-secondary)]">
              <LoaderCircle className="h-3.5 w-3.5 animate-spin text-[var(--brand)]" />
              Casting voices and rendering with ElevenLabs — this can take a few minutes…
            </p>
          ) : null}
          {audioError ? (
            <p className="text-[12px] text-destructive">{audioError}</p>
          ) : null}
          {audioSrc ? (
            <div className="space-y-2">
              <p className="text-[11px] font-semibold tracking-[0.14em] text-[var(--text-muted)] uppercase">
                Episode audio
                {audioStatus?.line_count ? ` · ${audioStatus.line_count} lines` : ''}
              </p>
              <audio controls className="w-full" src={audioSrc} preload="metadata">
                <track kind="captions" />
              </audio>
            </div>
          ) : null}
        </div>
      )}
    </article>
  )
}
