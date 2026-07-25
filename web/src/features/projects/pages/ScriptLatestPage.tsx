import { ArrowLeft } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { getLatestScript } from '../api/projects-api'
import type { ScriptLatest } from '../types'

export function ScriptLatestPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [script, setScript] = useState<ScriptLatest | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!projectId) return
    void (async () => {
      setLoading(true)
      try {
        setScript(await getLatestScript(projectId))
        setError(null)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load script')
      } finally {
        setLoading(false)
      }
    })()
  }, [projectId])

  return (
    <div className="mx-auto max-w-6xl">
      <Link
        to={`/projects/${projectId}`}
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to project
      </Link>
      <h1 className="mt-3 text-[22px] font-semibold tracking-tight text-[var(--text-primary)]">
        Latest script
      </h1>

      {loading ? (
        <p className="mt-6 text-[13px] text-[var(--text-secondary)]">Loading…</p>
      ) : null}
      {error ? <p className="mt-6 text-[13px] text-destructive">{error}</p> : null}

      {script ? (
        <div className="mt-6 space-y-4">
          <p className="text-[12px] text-[var(--text-secondary)]">
            Version {script.version} · run {script.run_id.slice(0, 8)}
          </p>
          <section className="rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-5">
            <h2 className="text-[14px] font-semibold text-[var(--text-primary)]">Screenplay</h2>
            <pre className="mt-4 max-h-[60vh] overflow-auto whitespace-pre-wrap font-sans text-[13px] leading-relaxed text-[var(--text-primary)]">
              {script.screenplay_md}
            </pre>
          </section>
          <section className="rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-5">
            <h2 className="text-[14px] font-semibold text-[var(--text-primary)]">Package JSON</h2>
            <pre className="mt-4 max-h-[40vh] overflow-auto rounded-[8px] bg-[var(--surface-0)] p-4 text-[11px] text-[var(--text-primary)]">
              {JSON.stringify(script.package, null, 2)}
            </pre>
          </section>
        </div>
      ) : null}
    </div>
  )
}
