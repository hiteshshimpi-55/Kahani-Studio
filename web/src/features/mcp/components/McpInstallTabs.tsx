import { useMemo, useState } from 'react'

import { cn } from '@/lib/utils'

import {
  installSnippet,
  installSteps,
  type InstallClient,
} from '../lib/catalog'
import { CopyButton } from './CopyButton'

const TABS: { id: InstallClient; label: string }[] = [
  { id: 'cursor', label: 'Cursor' },
  { id: 'claude-code', label: 'Claude Code' },
  { id: 'claude-desktop', label: 'Claude Desktop' },
]

type Props = {
  mcpUrl: string
  className?: string
}

export function McpInstallTabs({ mcpUrl, className }: Props) {
  const [tab, setTab] = useState<InstallClient>('cursor')
  const snippet = useMemo(() => installSnippet(tab, mcpUrl), [tab, mcpUrl])
  const steps = installSteps(tab)

  return (
    <section className={cn('mcp-enter-late space-y-3', className)}>
      <div>
        <h2 className="text-[16px] font-semibold tracking-tight text-[var(--text-primary)]">
          Connect
        </h2>
        <p className="mt-0.5 text-[13px] text-[var(--text-secondary)]">
          Paste the config into your agent client — same production stack as the studio.
        </p>
      </div>

      <div
        role="tablist"
        aria-label="MCP clients"
        className="flex flex-wrap gap-1 rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-0)] p-1"
      >
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              'rounded-[7px] px-3 py-1.5 text-[13px] font-medium transition-colors',
              tab === t.id
                ? 'bg-[var(--surface-2)] text-[var(--text-primary)] shadow-[0_1px_2px_rgba(0,0,0,0.04)]'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]',
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      <ol className="list-decimal space-y-1.5 pl-5 text-[13px] leading-5 text-[var(--text-secondary)]">
        {steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>

      <div className="overflow-hidden rounded-[12px] border border-[var(--folio-border)] bg-[var(--surface-0)]">
        <div className="flex items-center justify-between border-b border-[var(--folio-border)] px-3 py-2">
          <span className="text-[11px] font-semibold tracking-[0.1em] text-[var(--text-secondary)] uppercase">
            {tab === 'claude-code' ? 'CLI / config' : 'mcp.json'}
          </span>
          <CopyButton value={snippet} label="Copy snippet" />
        </div>
        <pre className="max-h-[280px] overflow-auto p-4 font-mono text-[12px] leading-5 text-[var(--text-primary)] whitespace-pre-wrap">
          {snippet}
        </pre>
      </div>
    </section>
  )
}
