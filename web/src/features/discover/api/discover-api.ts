import { apiUrl, parseJson } from '@/lib/api-client'
import type { TrendingTopicsResponse } from '../types'

export async function fetchTrendingTopics(
  region: string,
  state?: string,
  count = 8,
): Promise<TrendingTopicsResponse> {
  const params = new URLSearchParams({ region, count: String(count) })
  if (state) params.set('state', state)
  const res = await fetch(apiUrl(`/api/v1/discover/trending?${params.toString()}`))
  return parseJson<TrendingTopicsResponse>(res)
}
