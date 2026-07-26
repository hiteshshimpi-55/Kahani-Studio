import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ListingEmptyState, ListingShell, PageHeader } from '@/components/layout/PageHeader'
import { KissaLoader } from '@/components/ui/kissa-loader'
import { exportScript, getScript, listScripts } from '@/features/projects/api/projects-api'
import { useProject } from '@/features/projects/hooks/use-project'
import type { ScriptLatest, ScriptSummary } from '@/features/projects/types'
import { NotFoundView } from '@/features/system/pages/NotFoundPage'
import { apiUrl } from '@/lib/api-client'

type ExportFormat = 'markdown' | 'audio' | 'cover'

interface FormatMeta {
  id: ExportFormat
  label: string
  description: string
  ext: string
  icon: string
}

const FORMATS: FormatMeta[] = [
  {
    id: 'markdown',
    label: 'Markdown',
    description: 'Full screenplay with formatting preserved as .md',
    ext: 'md',
    icon: '📝',
  },
  {
    id: 'audio',
    label: 'Audio',
    description: 'Generated narration as .mp3 (if production was run)',
    ext: 'mp3',
    icon: '🎙️',
  },
  {
    id: 'cover',
    label: 'Cover Art',
    description: 'Generated cover image as .png (if visuals were produced)',
    ext: 'png',
    icon: '🖼️',
  },
]

function formatDate(iso: string) {
  try {
    return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(
      new Date(iso),
    )
  } catch {
    return iso
  }
}

export function ProjectExportPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { project, loading, error } = useProject(projectId)
  const [drafts, setDrafts] = useState<ScriptSummary[]>([])
  const [selected, setSelected] = useState<ScriptLatest | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [listError, setListError] = useState<string | null>(null)
  const [exporting, setExporting] = useState<ExportFormat | null>(null)
  const [exportError, setExportError] = useState<string | null>(null)

  useEffect(() => {
    if (!projectId) return
    void (async () => {
      try {
        const rows = await listScripts(projectId)
        setDrafts(rows)
        setListError(null)
        if (rows[0]) {
          setDetailLoading(true)
          try {
            setSelected(await getScript(projectId, rows[0].id))
          } finally {
            setDetailLoading(false)
          }
        }
      } catch (e) {
        setListError(e instanceof Error ? e.message : 'Failed to load drafts')
      }
    })()
  }, [projectId])

  async function selectDraft(id: string) {
    if (!projectId) return
    setDetailLoading(true)
    setExportError(null)
    try {
      setSelected(await getScript(projectId, id))
    } finally {
      setDetailLoading(false)
    }
  }

  async function handleExport(fmt: ExportFormat) {
    if (!selected || !projectId) return
    setExporting(fmt)
    setExportError(null)
    try {
      const result = await exportScript(projectId, selected.id, fmt)
      // For presigned S3 URLs the url is absolute; for local fallback it's a relative path.
      const downloadUrl = result.url.startsWith('http') ? result.url : apiUrl(result.url)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = result.filename
      a.target = '_blank'
      a.rel = 'noopener noreferrer'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    } catch (e) {
      setExportError(e instanceof Error ? e.message : 'Export failed')
    } finally {
      setExporting(null)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <KissaLoader label="Loading…" />
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
    <ListingShell maxWidth="5xl">
      <PageHeader
        title="Export"
        description="Store your script in S3 and download it in the format you need."
        breadcrumb={
          <Link to={`/projects/${project.id}/chat`} className="hover:text-[var(--brand)]">
            {project.name}
          </Link>
        }
      />

      {listError || drafts.length === 0 ? (
        <ListingEmptyState
          title="No drafts to export"
          description={
            listError || 'Generate a script in chat first — each run becomes a versioned draft.'
          }
          action={
            <Link
              to={`/projects/${project.id}/chat`}
              className="text-[13px] font-medium text-[var(--brand)] hover:underline"
            >
              Generate in chat
            </Link>
          }
        />
      ) : (
        <div className="space-y-6">
          {/* Draft selector */}
          <section>
            <h2 className="mb-2 text-[13px] font-semibold text-[var(--text-primary)]">
              Select draft
            </h2>
            <div className="flex flex-wrap gap-2">
              {drafts.map((d) => {
                const active = selected?.id === d.id
                return (
                  <button
                    key={d.id}
                    type="button"
                    onClick={() => void selectDraft(d.id)}
                    className={`rounded-[8px] border px-3 py-2 text-left transition-colors ${
                      active
                        ? 'border-[var(--brand)]/40 bg-[var(--surface-1)] text-[var(--text-primary)]'
                        : 'border-[var(--folio-border)] text-[var(--text-secondary)] hover:bg-[var(--surface-1)]'
                    }`}
                  >
                    <p className="text-[12px] font-semibold">
                      v{d.version}
                      {d.title ? ` · ${d.title}` : ''}
                    </p>
                    <p className="mt-0.5 text-[10px] text-[var(--text-muted)]">
                      {formatDate(d.created_at)}
                    </p>
                  </button>
                )
              })}
            </div>
          </section>

          {/* Format cards */}
          <section>
            <h2 className="mb-2 text-[13px] font-semibold text-[var(--text-primary)]">
              Choose format
            </h2>

            {exportError && (
              <p className="mb-3 rounded-[8px] border border-destructive/30 bg-destructive/5 px-3 py-2 text-[12px] text-destructive">
                {exportError}
              </p>
            )}

            {detailLoading ? (
              <div className="flex min-h-[120px] items-center justify-center">
                <KissaLoader size="sm" label="Loading draft…" />
              </div>
            ) : selected ? (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {FORMATS.map((fmt) => {
                  const busy = exporting === fmt.id
                  return (
                    <button
                      key={fmt.id}
                      type="button"
                      disabled={busy || exporting !== null}
                      onClick={() => void handleExport(fmt.id)}
                      className="group flex items-start gap-3 rounded-[10px] border border-[var(--folio-border)] p-4 text-left transition-colors hover:border-[var(--brand)]/40 hover:bg-[var(--surface-1)] disabled:opacity-50"
                    >
                      <span className="mt-0.5 text-[22px] leading-none">{fmt.icon}</span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5">
                          <span className="text-[13px] font-semibold text-[var(--text-primary)]">
                            {fmt.label}
                          </span>
                          <span className="rounded-[4px] bg-[var(--surface-0)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--text-muted)]">
                            .{fmt.ext}
                          </span>
                        </div>
                        <p className="mt-1 text-[12px] leading-snug text-[var(--text-secondary)]">
                          {fmt.description}
                        </p>
                        {busy && (
                          <p className="mt-1 text-[11px] text-[var(--brand)]">
                            Uploading to S3…
                          </p>
                        )}
                      </div>
                    </button>
                  )
                })}
              </div>
            ) : null}
          </section>

          {/* Selected draft preview */}
          {selected && !detailLoading && (
            <section className="rounded-[10px] border border-[var(--folio-border)] p-4">
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <h3 className="text-[13px] font-semibold">
                    Version {selected.version}
                    {selected.package?.title ? ` · ${selected.package.title}` : ''}
                  </h3>
                  <p className="mt-0.5 text-[11px] text-[var(--text-secondary)]">
                    Run {selected.run_id.slice(0, 8)} · Part {selected.part_number ?? 1}
                    {selected.package?.total_duration_sec
                      ? ` · ${Math.round(selected.package.total_duration_sec / 60)} min`
                      : ''}
                  </p>
                </div>
                <Link
                  to={`/projects/${project.id}/drafts?draft=${selected.id}`}
                  className="text-[12px] font-medium text-[var(--brand)] hover:underline"
                >
                  View draft
                </Link>
              </div>
              <pre className="max-h-[200px] overflow-auto font-sans text-[12px] leading-relaxed whitespace-pre-wrap text-[var(--text-secondary)]">
                {selected.screenplay_md?.slice(0, 800)}
                {(selected.screenplay_md?.length ?? 0) > 800 ? '\n…' : ''}
              </pre>
            </section>
          )}
        </div>
      )}
    </ListingShell>
  )
}
