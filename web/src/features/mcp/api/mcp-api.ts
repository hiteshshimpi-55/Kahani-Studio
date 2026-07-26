import { apiUrl, parseJson } from '@/lib/api-client'

import type { McpToolsCatalog } from '../types'

export async function fetchMcpToolsCatalog(): Promise<McpToolsCatalog> {
  const res = await fetch(apiUrl('/api/v1/agent/mcp/tools'))
  return parseJson(res)
}
