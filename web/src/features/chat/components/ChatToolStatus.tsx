import { Check, LoaderCircle, X } from 'lucide-react'

import { cn } from '@/lib/utils'

import type { AgentToolStep } from '../types'

export function ChatToolStatus({ tools }: { tools: AgentToolStep[] }) {
  return (
    <div className="my-3 space-y-1.5">
      {tools.map((tool) => (
        <div
          key={tool.id}
          className={cn(
            'chat-tool-enter flex w-fit max-w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-[12px]',
            tool.status === 'error'
              ? 'bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300'
              : 'bg-[var(--surface-1)] text-[var(--text-secondary)]',
          )}
        >
          {tool.status === 'running' ? (
            <LoaderCircle className="h-3.5 w-3.5 animate-spin text-[var(--brand)]" />
          ) : tool.status === 'done' ? (
            <Check className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
          ) : tool.status === 'error' ? (
            <X className="h-3.5 w-3.5" />
          ) : (
            <span className="h-3.5 w-3.5 rounded-full border border-[var(--folio-border-strong)]" />
          )}
          <span className="font-medium text-[var(--text-primary)]">{tool.label}</span>
          {tool.detail ? (
            <span className="hidden truncate sm:inline">· {tool.detail}</span>
          ) : null}
        </div>
      ))}
    </div>
  )
}
