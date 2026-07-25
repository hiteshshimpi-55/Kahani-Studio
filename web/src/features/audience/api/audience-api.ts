import { env } from '@/lib/env'

import type { EnqueueSimResponse, Patch, SimRun, SimulateRequest } from '../types'

function apiUrl(path: string) {
  return `${env.apiBaseUrl}/api/v1/audience${path}`
}

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`HTTP ${res.status}: ${text}`)
  }
  return (await res.json()) as T
}

export async function enqueueSimulation(req: SimulateRequest): Promise<EnqueueSimResponse> {
  const res = await fetch(apiUrl('/simulate'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  return parseJson(res)
}

export async function fetchSimRun(simRunId: string): Promise<SimRun> {
  const res = await fetch(apiUrl(`/runs/${simRunId}`))
  return parseJson(res)
}

export async function decidePatch(
  patchId: string,
  status: 'ACCEPTED' | 'REJECTED',
): Promise<Patch> {
  const res = await fetch(apiUrl(`/patches/${patchId}`), {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  })
  return parseJson(res)
}
