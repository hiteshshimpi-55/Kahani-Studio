import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchTrendingTopics } from '../api/discover-api'
import type { TrendingTopicsResponse } from '../types'

type FetchState = {
  data: TrendingTopicsResponse | null
  loading: boolean
  error: string | null
}

export function useTrendingTopics(region: string, state?: string) {
  const [fetchState, setFetchState] = useState<FetchState>({
    data: null,
    loading: false,
    error: null,
  })
  const abortRef = useRef<AbortController | null>(null)

  const load = useCallback(async (r: string, s?: string) => {
    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    setFetchState({ data: null, loading: true, error: null })
    try {
      const data = await fetchTrendingTopics(r, s)
      if (!ctrl.signal.aborted) setFetchState({ data, loading: false, error: null })
    } catch (err) {
      if (!ctrl.signal.aborted) {
        setFetchState({ data: null, loading: false, error: (err as Error).message })
      }
    }
  }, [])

  useEffect(() => {
    void load(region, state)
    return () => abortRef.current?.abort()
  }, [region, state, load])

  const refresh = useCallback(() => void load(region, state), [region, state, load])

  return { ...fetchState, refresh }
}
