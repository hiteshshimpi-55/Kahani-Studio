import { apiUrl, parseJson } from '@/lib/api-client'

import type { EnqueuePingResponse, HealthResponse } from '../types'

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(apiUrl('/api/health'))
  return parseJson(res)
}

export async function enqueuePingJob(): Promise<EnqueuePingResponse> {
  const res = await fetch(apiUrl('/api/v1/jobs/ping'), { method: 'POST' })
  return parseJson(res)
}
