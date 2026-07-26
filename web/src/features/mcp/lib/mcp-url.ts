import { env } from '@/lib/env'

/** Resolve the public MCP URL for copy + install snippets. */
export function resolveMcpUrl(catalogUrl?: string | null): string {
  let url = ''
  if (env.mcpUrl) url = env.mcpUrl
  else if (catalogUrl?.trim()) url = catalogUrl.trim()
  else {
    const base = env.apiBaseUrl || (typeof window !== 'undefined' ? window.location.origin : '')
    url = base ? `${base.replace(/\/$/, '')}/mcp` : 'http://localhost:8000/mcp'
  }
  // Mounted Streamable HTTP expects a trailing slash (Starlette Mount redirect).
  return url.endsWith('/') ? url : `${url}/`
}

