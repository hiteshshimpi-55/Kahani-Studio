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
}

const ACCEPT = '.md,.txt,.markdown,text/plain,text/markdown'

export function ContextAttachmentsPanel({
  attachments,
  loading,
  uploading,
  error,
  onUpload,
  onDelete,
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
    <section className="rounded-lg border border-border bg-card p-5">
      <div className="mb-4">
        <h2 className="text-base font-semibold">Context</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Attachments ground generation. Upload briefs, research, or source notes.
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
          'flex cursor-pointer flex-col items-center justify-center rounded-md border border-dashed px-4 py-8 text-center transition-colors',
          dragging ? 'border-primary bg-primary/5' : 'border-border bg-muted/40 hover:bg-muted/60',
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
        <p className="text-sm font-medium text-foreground">
          {uploading ? 'Uploading…' : 'Drop files or click to upload'}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">.md, .txt, .markdown</p>
      </label>

      {error ? <p className="mt-3 text-sm text-destructive">{error}</p> : null}

      <div className="mt-4 space-y-2">
        {loading && attachments.length === 0 ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : null}
        {!loading && attachments.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Upload briefs, research, or source notes to ground generation.
          </p>
        ) : null}
        {attachments.map((a) => (
          <div
            key={a.id}
            className="flex items-start justify-between gap-3 rounded-md border border-border bg-background/60 px-3 py-2"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{a.filename}</p>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <span className="text-xs text-muted-foreground">{formatBytes(a.size_bytes)}</span>
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
