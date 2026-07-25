import { useCallback, useEffect, useRef, useState } from 'react'

import * as api from '../api/projects-api'
import type { ProjectRun, StartRunInput } from '../types'

export function useProjectRun(projectId: string | undefined) {
  const [run, setRun] = useState<ProjectRun | null>(null)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollRef = useRef<number | null>(null)

  const stopPoll = useCallback(() => {
    if (pollRef.current) {
      window.clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  useEffect(() => () => stopPoll(), [stopPoll])

  const poll = useCallback(
    (runId: string) => {
      if (!projectId) return
      stopPoll()
      pollRef.current = window.setInterval(async () => {
        try {
          const next = await api.getRun(projectId, runId)
          setRun(next)
          if (next.status === 'succeeded' || next.status === 'failed') {
            stopPoll()
          }
        } catch {
          /* keep polling */
        }
      }, 2000)
    },
    [projectId, stopPoll],
  )

  const start = useCallback(
    async (input: StartRunInput) => {
      if (!projectId) return
      setStarting(true)
      setError(null)
      try {
        const created = await api.startRun(projectId, input)
        setRun(created)
        if (created.status === 'queued' || created.status === 'running') {
          poll(created.id)
        }
        return created
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to start run')
        return null
      } finally {
        setStarting(false)
      }
    },
    [projectId, poll],
  )

  const busy = starting || run?.status === 'queued' || run?.status === 'running'

  return { run, starting, busy, error, start }
}
