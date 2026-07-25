import { useAudienceSim } from '@/features/audience/hooks/use-audience-sim'

import { AuditCard } from './AuditCard'
import { EngagementCard } from './EngagementCard'
import { PatchList } from './PatchList'
import { SimulateForm } from './SimulateForm'

export function AudienceSimView() {
  const { simRun, error, busy, runSimulation, handlePatchDecision } = useAudienceSim()

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-8 px-6 py-12">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">
          Audience simulation
        </h1>
        <p className="text-stone-600">
          Structural audit + persona simulation. Paste a script, run the sim,
          review patches.
        </p>
      </header>

      {/* Form */}
      <section className="rounded-lg border border-stone-300 bg-[#faf7f0] p-5">
        <SimulateForm onSubmit={runSimulation} busy={busy} />
      </section>

      {/* Error */}
      {error && <p className="text-sm text-red-700">{error}</p>}

      {/* Status */}
      {simRun && (
        <div className="flex items-center gap-3 text-sm">
          <span className="text-stone-500">Status:</span>
          <StatusBadge status={simRun.status} />
          {simRun.status === 'RUNNING' && (
            <span className="text-xs text-stone-400 animate-pulse">
              Processing…
            </span>
          )}
        </div>
      )}

      {/* Results */}
      {simRun?.status === 'COMPLETED' && (
        <>
          {simRun.audit && <AuditCard audit={simRun.audit} />}
          {simRun.engagement && <EngagementCard engagement={simRun.engagement} />}
          <PatchList patches={simRun.patches} onDecide={handlePatchDecision} />
        </>
      )}

      {/* Error state */}
      {simRun?.status === 'FAILED' && (
        <div className="rounded border border-red-200 bg-red-50 p-4">
          <p className="text-sm font-medium text-red-800">Simulation failed</p>
          {simRun.error && (
            <p className="mt-1 font-mono text-xs text-red-600">{simRun.error}</p>
          )}
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    PENDING: 'bg-stone-200 text-stone-700',
    RUNNING: 'bg-blue-100 text-blue-800',
    COMPLETED: 'bg-green-100 text-green-800',
    FAILED: 'bg-red-100 text-red-800',
  }
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[status] || ''}`}>
      {status}
    </span>
  )
}
