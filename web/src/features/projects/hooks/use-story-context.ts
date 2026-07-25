import { useCallback, useEffect, useState } from 'react'

import * as api from '../api/projects-api'
import type { ProjectCharacter, ScriptSummary } from '../types'

export function useStoryCast(projectId: string | undefined) {
  const [characters, setCharacters] = useState<ProjectCharacter[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      const rows = await api.listCharacters(projectId)
      setCharacters(rows)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load cast')
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const update = useCallback(
    async (
      id: string,
      body: Partial<Pick<ProjectCharacter, 'name' | 'role' | 'voice' | 'speech_patterns' | 'arc'>>,
    ) => {
      if (!projectId) return
      const updated = await api.updateCharacter(projectId, id, body)
      setCharacters((prev) => prev.map((c) => (c.id === id ? updated : c)))
    },
    [projectId],
  )

  const remove = useCallback(
    async (id: string) => {
      if (!projectId) return
      await api.deleteCharacter(projectId, id)
      setCharacters((prev) => prev.filter((c) => c.id !== id))
    },
    [projectId],
  )

  return { characters, loading, error, refresh, update, remove }
}

export function useStoryEpisodes(projectId: string | undefined) {
  const [episodes, setEpisodes] = useState<ScriptSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      const rows = await api.listScripts(projectId)
      setEpisodes(rows)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load episodes')
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const pin = useCallback(
    async (scriptId: string, pinned: boolean) => {
      if (!projectId) return
      const updated = await api.pinScript(projectId, scriptId, pinned)
      setEpisodes((prev) => prev.map((e) => (e.id === scriptId ? updated : e)))
    },
    [projectId],
  )

  return { episodes, loading, error, refresh, pin }
}

export function useStoryContextSummary(projectId: string | undefined) {
  const [summary, setSummary] = useState<{
    cast_count: number
    docs_count: number
    episode_count: number
    latest_part_number: number | null
  } | null>(null)

  const refresh = useCallback(async () => {
    if (!projectId) return
    try {
      setSummary(await api.getStoryContextSummary(projectId))
    } catch {
      /* optional chip */
    }
  }, [projectId])

  useEffect(() => {
    void refresh()
  }, [refresh])

  return { summary, refresh }
}
