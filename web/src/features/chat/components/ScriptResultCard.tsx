import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

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
  onSaveDraft?: (text?: string) => void | Promise<void>
  onUpdateDraft?: (text: string) => void | Promise<void>
}) {
  const [editing, setEditing] = useState(false)
  const [draftText, setDraftText] = useState(preview)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!editing) setDraftText(preview)
  }, [preview, editing])

  const draftsHref = scriptId
    ? `/projects/${projectId}/drafts?draft=${scriptId}`
    : `/projects/${projectId}/drafts`
  const editorHref = scriptId
    ? `/editor?project=${projectId}&draft=${scriptId}`
    : `/projects/${projectId}/drafts`

  return (
    <article className="chat-tool-enter my-3 overflow-hidden rounded-[16px] border border-[var(--folio-border-strong)] bg-[var(--surface-2)] shadow-[var(--shadow-card)]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--folio-border)] px-4 py-3">
        <p className="text-[11px] font-semibold tracking-[0.14em] text-[var(--text-muted)] uppercase">
          {isDraft ? 'Saved draft' : 'Script output'}
        </p>
        <div className="flex flex-wrap items-center gap-3">
          {!isDraft && runId && onSaveDraft ? (
            <button
              type="button"
              disabled={busy}
              className="text-[12px] font-medium text-[var(--brand)] hover:underline disabled:opacity-50"
              onClick={() => {
                void (async () => {
                  setBusy(true)
                  try {
                    await onSaveDraft(editing ? draftText : undefined)
                    setEditing(false)
                  } finally {
                    setBusy(false)
                  }
                })()
              }}
            >
              {busy ? 'Saving…' : 'Add as draft'}
            </button>
          ) : null}
          {(isDraft ? onUpdateDraft : onSaveDraft) ? (
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
          {isDraft && scriptId ? (
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
          {isDraft && onUpdateDraft ? (
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
    </article>
  )
}
