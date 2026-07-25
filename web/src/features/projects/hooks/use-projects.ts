import { useCallback, useEffect, useState } from 'react'

import * as api from '../api/projects-api'
import type { CreateProjectInput, Project } from '../types'

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setProjects(await api.listProjects())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load projects')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const create = useCallback(async (input: CreateProjectInput) => {
    const project = await api.createProject(input)
    setProjects((prev) => [project, ...prev])
    return project
  }, [])

  return { projects, loading, error, refresh, create }
}
