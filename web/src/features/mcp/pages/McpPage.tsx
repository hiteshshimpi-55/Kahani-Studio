import { useEffect, useState } from 'react'

import { BrandMark } from '@/components/brand/BrandMark'
import { ListingShell } from '@/components/layout/PageHeader'
import { apiUrl, parseJson } from '@/lib/api-client'

import { fetchMcpToolsCatalog } from '../api/mcp-api'
import { McpConnectionCard } from '../components/McpConnectionCard'
import { McpInstallTabs } from '../components/McpInstallTabs'
import { McpToolsList } from '../components/McpToolsList'
import { FALLBACK_TOOLS } from '../lib/catalog'
import { resolveMcpUrl } from '../lib/mcp-url'
import type { McpToolCatalogItem } from '../types'

export function McpPage() {
  const [tools, setTools] = useState<McpToolCatalogItem[]>(FALLBACK_TOOLS)
  const [mcpUrl, setMcpUrl] = useState(() => resolveMcpUrl())
  const [live, setLive] = useState<boolean | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const catalog = await fetchMcpToolsCatalog()
        if (cancelled) return
        if (catalog.tools?.length) setTools(catalog.tools)
        setMcpUrl(resolveMcpUrl(catalog.mcp_url))
      } catch {
        if (!cancelled) setMcpUrl(resolveMcpUrl())
      }
      try {
        const health = await parseJson<{ status?: string }>(
          await fetch(apiUrl('/api/health/live')),
        )
        if (!cancelled) setLive(health?.status === 'ok')
      } catch {
        if (!cancelled) setLive(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <ListingShell maxWidth="4xl" className="pb-10">
      <header className="mcp-enter mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex items-start gap-3.5">
          <BrandMark size={48} className="rounded-[12px]" />
          <div>
            <h1 className="text-[26px] font-semibold tracking-tight text-[var(--text-primary)]">
              Kahani MCP
            </h1>
            <p className="mt-1 max-w-xl text-[14px] leading-6 text-[var(--text-secondary)]">
              Plug Kahani into your coding agent. Tools produce a listen-ready episode{' '}
              <span className="text-[var(--text-primary)]">audio URL</span> from a story brief.
            </p>
          </div>
        </div>
      </header>

      <div className="space-y-8">
        <McpConnectionCard mcpUrl={mcpUrl} live={live} />
        <McpToolsList tools={tools} />
        <McpInstallTabs mcpUrl={mcpUrl} />
      </div>
    </ListingShell>
  )
}
