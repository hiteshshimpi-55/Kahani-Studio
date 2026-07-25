import { useCallback, useEffect, useRef, useState } from 'react'

import {
  getProjectAudienceSimLatest,
  triggerProjectAudienceSim,
} from '@/features/projects/api/projects-api'
import { decidePatch } from '@/features/audience/api/audience-api'

import type { Patch, SimRun } from '../types'

export function useProjectAudienceSim(projectId: string | null) {
  const [simRun, setSimRun] = useState<SimRun | null>(null)
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const startPolling = useCallback(
    (pid: string) => {
      stopPolling()
      pollRef.current = setInterval(async () => {
        try {
          const run = (await getProjectAudienceSimLatest(pid)) as SimRun | null
          if (!run) return
          setSimRun(run)
          if (run.status === 'COMPLETED' || run.status === 'FAILED') {
            stopPolling()
            setBusy(false)
          }
        } catch {
          // silently retry
        }
      }, 2000)
    },
    [stopPolling],
  )

  // Load latest run whenever the selected project changes
  useEffect(() => {
    stopPolling()
    setSimRun(null)
    setError(null)
    if (!projectId) return

    setLoading(true)
    void getProjectAudienceSimLatest(projectId)
      .then((run) => {
        const typed = run as SimRun | null
        setSimRun(typed)
        if (typed?.status === 'PENDING' || typed?.status === 'RUNNING') {
          setBusy(true)
          startPolling(projectId)
        }
      })
      .catch(() => {/* no run yet */})
      .finally(() => setLoading(false))

    return stopPolling
  }, [projectId, startPolling, stopPolling])

  const runSimulation = useCallback(
    async (genre: string, language: string, partCount: number) => {
      if (!projectId) return
      setBusy(true)
      setError(null)
      try {
        await triggerProjectAudienceSim(projectId, {
          genre,
          language,
          part_count: partCount,
        })
        startPolling(projectId)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to start simulation')
        setBusy(false)
      }
    },
    [projectId, startPolling],
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

  return { simRun, loading, busy, error, runSimulation, handlePatchDecision }
}
