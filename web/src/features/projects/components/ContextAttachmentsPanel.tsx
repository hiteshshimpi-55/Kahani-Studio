import { Upload } from 'lucide-react'
import { useCallback, useState, type DragEvent } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

import type { IndexStatus, ProjectAttachment } from '../types'

function formatBytes(n: number) {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

function statusTone(status: IndexStatus) {
  if (status === 'indexed') return 'success' as const
  if (status === 'failed') return 'danger' as const
  return 'warning' as const
}

interface Props {
  attachments: ProjectAttachment[]
  loading: boolean
  uploading: boolean
  error: string | null
  onUpload: (files: FileList | File[]) => Promise<void>
  onDelete: (id: string) => Promise<void>
  /** When false, upload only via page + Add CTA */
  showDropzone?: boolean
}

const ACCEPT = '.md,.txt,.markdown,text/plain,text/markdown'

export function ContextAttachmentsPanel({
  attachments,
  loading,
  uploading,
  error,
  onUpload,
  onDelete,
  showDropzone = true,
}: Props) {
  const [dragging, setDragging] = useState(false)

  const onDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault()
      setDragging(false)
      if (e.dataTransfer.files?.length) {
        void onUpload(e.dataTransfer.files)
      }
    },
    [onUpload],
  )

  return (
    <section className="rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-5">
      {showDropzone ? (
        <>
          <div className="mb-4">
            <h2 className="text-[14px] font-semibold text-[var(--text-primary)]">Context</h2>
            <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
              Add briefs the agent should know.
            </p>
          </div>

          <label
            onDragOver={(e) => {
              e.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            className={cn(
              'flex cursor-pointer flex-col items-center justify-center rounded-[8px] border border-dashed px-4 py-8 text-center transition-colors',
              dragging
                ? 'border-[var(--brand)] bg-[var(--brand)]/5'
                : 'border-[var(--folio-border)] bg-[var(--surface-0)] hover:bg-[var(--surface-1)]',
            )}
          >
            <input
              type="file"
              className="sr-only"
              accept={ACCEPT}
              multiple
              disabled={uploading}
              onChange={(e) => {
                if (e.target.files?.length) void onUpload(e.target.files)
                e.target.value = ''
              }}
            />
            <Upload className="mb-2 h-4 w-4 stroke-[1.75] text-[var(--text-secondary)]" />
            <p className="text-[13px] font-medium text-[var(--text-primary)]">
              {uploading ? 'Uploading…' : 'Drop files or click to upload'}
            </p>
            <p className="mt-1 text-[11px] text-[var(--text-secondary)]">.md, .txt, .markdown</p>
          </label>
        </>
      ) : null}

      {error ? <p className={cn('text-[13px] text-destructive', showDropzone && 'mt-3')}>{error}</p> : null}

      <div className={cn('space-y-2', (showDropzone || error) && 'mt-4')}>
        {loading && attachments.length === 0 ? (
          <p className="text-[13px] text-[var(--text-secondary)]">Loading…</p>
        ) : null}
        {!loading && attachments.length === 0 ? (
          <p className="text-[13px] text-[var(--text-secondary)]">
            Use + Add to upload briefs, research, or source notes.
          </p>
        ) : null}
        {attachments.map((a) => (
          <div
            key={a.id}
            className="flex items-start justify-between gap-3 rounded-[8px] border border-[var(--folio-border)] bg-[var(--surface-0)] px-3 py-2"
          >
            <div className="min-w-0">
              <p className="truncate text-[13px] font-medium text-[var(--text-primary)]">
                {a.filename}
              </p>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <span className="text-[11px] text-[var(--text-secondary)]">
                  {formatBytes(a.size_bytes)}
                </span>
                <Badge tone={statusTone(a.index_status)}>{a.index_status}</Badge>
              </div>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => void onDelete(a.id)}
              aria-label={`Delete ${a.filename}`}
            >
              Delete
            </Button>
          </div>
        ))}
      </div>
    </section>
  )
}
