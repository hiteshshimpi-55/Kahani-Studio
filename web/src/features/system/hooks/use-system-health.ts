import { useCallback, useEffect, useState } from 'react'

import { enqueuePingJob, fetchHealth } from '@/features/system/api/system-api'
import type { HealthResponse } from '@/features/system/types'

export function useSystemHealth() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const loadHealth = useCallback(async () => {
    setError(null)
    try {
      setHealth(await fetchHealth())
    } catch (e) {
      setHealth(null)
      setError(e instanceof Error ? e.message : 'Failed to reach API')
    }
  }, [])

  const enqueuePing = useCallback(async () => {
    setBusy(true)
    setError(null)
    try {
      const data = await enqueuePingJob()
      setJobId(data.job_id)
      await loadHealth()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to enqueue job')
    } finally {
      setBusy(false)
    }
  }, [loadHealth])

  useEffect(() => {
    void loadHealth()
  }, [loadHealth])

  return { health, error, jobId, busy, loadHealth, enqueuePing }
}
