import { useCallback, useEffect, useSyncExternalStore } from 'react'

import * as api from '../api/projects-api'
import type { CreateProjectInput, Project } from '../types'

type ProjectsState = {
  projects: Project[]
  loading: boolean
  error: string | null
  hydrated: boolean
}

let state: ProjectsState = {
  projects: [],
  loading: true,
  error: null,
  hydrated: false,
}

const listeners = new Set<() => void>()

function emit() {
  for (const listener of listeners) listener()
}

function setState(patch: Partial<ProjectsState>) {
  state = { ...state, ...patch }
  emit()
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

function getSnapshot() {
  return state
}

let refreshPromise: Promise<void> | null = null

async function refreshProjects() {
  if (refreshPromise) return refreshPromise
  setState({ loading: true, error: null })
  refreshPromise = (async () => {
    try {
      const projects = await api.listProjects()
      setState({ projects, loading: false, error: null, hydrated: true })
    } catch (e) {
      setState({
        loading: false,
        error: e instanceof Error ? e.message : 'Failed to load projects',
        hydrated: true,
      })
    } finally {
      refreshPromise = null
    }
  })()
  return refreshPromise
}

function ensureHydrated() {
  if (!state.hydrated && !refreshPromise) {
    void refreshProjects()
  }
}

export function useProjects() {
  const snapshot = useSyncExternalStore(subscribe, getSnapshot, getSnapshot)

  useEffect(() => {
    ensureHydrated()
  }, [])

  const refresh = useCallback(async () => {
    await refreshProjects()
  }, [])

  const create = useCallback(async (input: CreateProjectInput) => {
    const project = await api.createProject(input)
    setState({ projects: [project, ...state.projects] })
    return project
  }, [])

  const remove = useCallback(async (projectId: string) => {
    await api.deleteProject(projectId)
    setState({ projects: state.projects.filter((p) => p.id !== projectId) })
  }, [])

  return {
    projects: snapshot.projects,
    loading: snapshot.loading,
    error: snapshot.error,
    refresh,
    create,
    remove,
  }
}
