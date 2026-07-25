import { env } from '@/lib/env'

import type { EnqueuePingResponse, HealthResponse } from '../types'

function apiUrl(path: string) {
  return `${env.apiBaseUrl}${path}`
}

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`)
  }
  return (await res.json()) as T
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(apiUrl('/api/health'))
  return parseJson(res)
}

export async function enqueuePingJob(): Promise<EnqueuePingResponse> {
  const res = await fetch(apiUrl('/api/v1/jobs/ping'), { method: 'POST' })
  return parseJson(res)
}
