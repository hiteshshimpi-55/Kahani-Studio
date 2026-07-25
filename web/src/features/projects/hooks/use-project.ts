import { useCallback, useEffect, useState } from 'react'

import * as api from '../api/projects-api'
import type { Project } from '../types'

export function useProject(projectId: string | undefined) {
  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      setProject(await api.getProject(projectId))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load project')
      setProject(null)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    void refresh()
  }, [refresh])

  return { project, loading, error, refresh }
}
