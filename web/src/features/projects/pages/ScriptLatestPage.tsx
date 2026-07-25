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
    <main className="mx-auto max-w-6xl px-6 py-10">
      <Link
        to={`/projects/${projectId}`}
        className="text-sm text-muted-foreground hover:text-primary"
      >
        ← Back to project
      </Link>
      <h1 className="mt-4 text-2xl font-bold tracking-tight">Latest script</h1>

      {loading ? <p className="mt-6 text-sm text-muted-foreground">Loading…</p> : null}
      {error ? <p className="mt-6 text-sm text-destructive">{error}</p> : null}

      {script ? (
        <div className="mt-8 space-y-8">
          <p className="text-sm text-muted-foreground">
            Version {script.version} · run {script.run_id.slice(0, 8)}
          </p>
          <section className="rounded-lg border border-border bg-card p-5">
            <h2 className="text-base font-semibold">Screenplay</h2>
            <pre className="mt-4 max-h-[60vh] overflow-auto whitespace-pre-wrap font-sans text-sm leading-relaxed text-foreground">
              {script.screenplay_md}
            </pre>
          </section>
          <section className="rounded-lg border border-border bg-card p-5">
            <h2 className="text-base font-semibold">Package JSON</h2>
            <pre className="mt-4 max-h-[40vh] overflow-auto rounded-md bg-muted/50 p-4 text-xs">
              {JSON.stringify(script.package, null, 2)}
            </pre>
          </section>
        </div>
      ) : null}
    </main>
  )
}
