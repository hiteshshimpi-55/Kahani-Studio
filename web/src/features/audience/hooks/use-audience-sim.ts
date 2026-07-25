import { useCallback, useRef, useState } from 'react'

import {
  decidePatch,
  enqueueSimulation,
  fetchSimRun,
} from '@/features/audience/api/audience-api'
import type { Patch, SimRun, SimulateRequest } from '@/features/audience/types'

export function useAudienceSim() {
  const [simRun, setSimRun] = useState<SimRun | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const pollStatus = useCallback(
    (simRunId: string) => {
      stopPolling()
      pollRef.current = setInterval(async () => {
        try {
          const run = await fetchSimRun(simRunId)
          setSimRun(run)
          if (run.status === 'COMPLETED' || run.status === 'FAILED') {
            stopPolling()
          }
        } catch {
          // Silently retry on poll errors
        }
      }, 2000)
    },
    [stopPolling],
  )

  const runSimulation = useCallback(
    async (req: SimulateRequest) => {
      setBusy(true)
      setError(null)
      setSimRun(null)
      stopPolling()
      try {
        const { sim_run_id } = await enqueueSimulation(req)
        // Fetch initial state
        const run = await fetchSimRun(sim_run_id)
        setSimRun(run)
        // Start polling if not already done
        if (run.status === 'PENDING' || run.status === 'RUNNING') {
          pollStatus(sim_run_id)
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to start simulation')
      } finally {
        setBusy(false)
      }
    },
    [pollStatus, stopPolling],
  )

  const handlePatchDecision = useCallback(
    async (patchId: string, accepted: boolean) => {
      try {
        const updated: Patch = await decidePatch(patchId, accepted ? 'ACCEPTED' : 'REJECTED')
        setSimRun((prev) => {
          if (!prev) return prev
          return {
            ...prev,
            patches: prev.patches.map((p) => (p.id === updated.id ? updated : p)),
          }
        })
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to update patch')
      }
    },
    [],
  )

  return { simRun, error, busy, runSimulation, handlePatchDecision, stopPolling }
}
