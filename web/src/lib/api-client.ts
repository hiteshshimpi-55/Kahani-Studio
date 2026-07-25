import { env } from '@/lib/env'

export function apiUrl(path: string) {
  return `${env.apiBaseUrl}${path}`
}

export async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const body = (await res.json()) as { message?: string; detail?: string }
      detail = body.message || body.detail || detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  return (await res.json()) as T
}
