import { useState } from 'react'

import { useProjects } from '@/features/projects/hooks/use-projects'
import { useAudienceSim } from '@/features/audience/hooks/use-audience-sim'
import { useProjectAudienceSim } from '@/features/audience/hooks/use-project-audience-sim'

import { AuditCard } from './AuditCard'
import { EngagementCard } from './EngagementCard'
import { PatchList } from './PatchList'
import { SimulateForm } from './SimulateForm'

type Mode = 'project' | 'manual'

const GENRES = ['thriller', 'romance', 'drama', 'biopic', 'horror', 'comedy']
const LANGUAGES = ['hindi', 'english']

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    PENDING: 'bg-stone-200 text-stone-700',
    RUNNING: 'bg-blue-100 text-blue-800',
    COMPLETED: 'bg-green-100 text-green-800',
    FAILED: 'bg-red-100 text-red-800',
  }
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[status] ?? ''}`}>
      {status}
    </span>
  )
}

function ProjectSimResults({
  projectId,
}: {
  projectId: string
}) {
  const [genre, setGenre] = useState('thriller')
  const [language, setLanguage] = useState('hindi')
  const { simRun, loading, busy, error, runSimulation, handlePatchDecision } =
    useProjectAudienceSim(projectId)

  return (
    <div className="flex flex-col gap-6">
      {/* Run controls */}
      <section className="rounded-lg border border-stone-300 bg-[#faf7f0] p-5">
        <h3 className="mb-3 text-sm font-medium text-stone-700">Run audience simulation</h3>
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-stone-500">Genre</span>
            <select
              className="rounded border border-stone-300 bg-white px-3 py-1.5 text-sm"
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
            >
              {GENRES.map((g) => (
                <option key={g} value={g}>
                  {g.charAt(0).toUpperCase() + g.slice(1)}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-stone-500">Language</span>
            <select
              className="rounded border border-stone-300 bg-white px-3 py-1.5 text-sm"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {LANGUAGES.map((l) => (
                <option key={l} value={l}>
                  {l.charAt(0).toUpperCase() + l.slice(1)}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            disabled={busy}
            onClick={() => void runSimulation(genre, language, 5)}
            className="self-end rounded bg-stone-900 px-5 py-1.5 text-sm text-stone-50 disabled:opacity-50"
          >
            {busy ? 'Running…' : simRun ? 'Re-run' : 'Run simulation'}
          </button>
        </div>
        {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
      </section>

      {loading && (
        <p className="text-sm text-stone-400 animate-pulse">Loading previous results…</p>
      )}

      {simRun && (
        <>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-stone-500">Status:</span>
            <StatusBadge status={simRun.status} />
            {(simRun.status === 'PENDING' || simRun.status === 'RUNNING') && (
              <span className="text-xs text-stone-400 animate-pulse">
                Simulating 24 personas…
              </span>
            )}
          </div>

          {simRun.status === 'COMPLETED' && (
            <>
              {simRun.audit && <AuditCard audit={simRun.audit} />}
              {simRun.engagement && <EngagementCard engagement={simRun.engagement} />}
              <PatchList patches={simRun.patches} onDecide={handlePatchDecision} />
            </>
          )}

          {simRun.status === 'FAILED' && (
            <div className="rounded border border-red-200 bg-red-50 p-4">
              <p className="text-sm font-medium text-red-800">Simulation failed</p>
              {simRun.error && (
                <p className="mt-1 font-mono text-xs text-red-600">{simRun.error}</p>
              )}
            </div>
          )}
        </>
      )}

      {!loading && !simRun && (
        <p className="text-sm text-stone-400">
          No simulation run yet for this project. Hit "Run simulation" to start.
        </p>
      )}
    </div>
  )
}

export function AudienceSimView() {
  const [mode, setMode] = useState<Mode>('project')
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const { projects, loading: projectsLoading } = useProjects()

  // Manual mode state
  const { simRun, error, busy, runSimulation: runManual, handlePatchDecision } = useAudienceSim()

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-8 px-6 py-12">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">Audience simulation</h1>
        <p className="text-stone-600">
          Structural audit + 24-persona simulation. Review engagement funnels and patch suggestions.
        </p>
      </header>

      {/* Mode toggle */}
      <div className="flex gap-1 rounded-lg border border-stone-200 bg-stone-100 p-1 w-fit">
        <button
          type="button"
          onClick={() => setMode('project')}
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
            mode === 'project'
              ? 'bg-white text-stone-900 shadow-sm'
              : 'text-stone-500 hover:text-stone-700'
          }`}
        >
          By project
        </button>
        <button
          type="button"
          onClick={() => setMode('manual')}
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
            mode === 'manual'
              ? 'bg-white text-stone-900 shadow-sm'
              : 'text-stone-500 hover:text-stone-700'
          }`}
        >
          Paste script
        </button>
      </div>

      {/* Project mode */}
      {mode === 'project' && (
        <div className="flex flex-col gap-6">
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-stone-700">Select project</label>
            {projectsLoading ? (
              <p className="text-sm text-stone-400 animate-pulse">Loading projects…</p>
            ) : (
              <select
                className="rounded border border-stone-300 bg-white px-3 py-2 text-sm max-w-sm"
                value={selectedProjectId ?? ''}
                onChange={(e) => setSelectedProjectId(e.target.value || null)}
              >
                <option value="">— choose a project —</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          {selectedProjectId && (
            <ProjectSimResults key={selectedProjectId} projectId={selectedProjectId} />
          )}

          {!selectedProjectId && !projectsLoading && (
            <p className="text-sm text-stone-400">
              Pick a project above to see or run its audience analysis.
            </p>
          )}
        </div>
      )}

      {/* Manual mode */}
      {mode === 'manual' && (
        <div className="flex flex-col gap-6">
          <section className="rounded-lg border border-stone-300 bg-[#faf7f0] p-5">
            <SimulateForm onSubmit={runManual} busy={busy} />
          </section>

          {error && <p className="text-sm text-red-700">{error}</p>}

          {simRun && (
            <>
              <div className="flex items-center gap-3 text-sm">
                <span className="text-stone-500">Status:</span>
                <StatusBadge status={simRun.status} />
                {simRun.status === 'RUNNING' && (
                  <span className="text-xs text-stone-400 animate-pulse">Processing…</span>
                )}
              </div>

              {simRun.status === 'COMPLETED' && (
                <>
                  {simRun.audit && <AuditCard audit={simRun.audit} />}
                  {simRun.engagement && <EngagementCard engagement={simRun.engagement} />}
                  <PatchList patches={simRun.patches} onDecide={handlePatchDecision} />
                </>
              )}

              {simRun.status === 'FAILED' && (
                <div className="rounded border border-red-200 bg-red-50 p-4">
                  <p className="text-sm font-medium text-red-800">Simulation failed</p>
                  {simRun.error && (
                    <p className="mt-1 font-mono text-xs text-red-600">{simRun.error}</p>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
