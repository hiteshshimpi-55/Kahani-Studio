import { RotateCcw } from 'lucide-react'

import type { ChatSession } from '@/features/projects/types'
import { cn } from '@/lib/utils'

type Props = {
  sessions: ChatSession[]
  activeSessionId: string | null
  streaming?: boolean
  onSelect: (sessionId: string) => void
  onReset: () => void
}

export function ChatSessionsPanel({
  sessions,
  activeSessionId,
  streaming,
  onSelect,
  onReset,
}: Props) {
  return (
    <aside className="hidden h-full w-[220px] shrink-0 flex-col border-l border-[var(--folio-border)] bg-[var(--surface-2)] lg:flex">
      <div className="flex items-center justify-between gap-2 border-b border-[var(--folio-border)] px-3 py-3">
        <p className="text-[11px] font-semibold tracking-[0.12em] text-[var(--text-muted)] uppercase">
          Sessions
        </p>
        <button
          type="button"
          disabled={streaming}
          onClick={onReset}
          title="Reset session"
          className="inline-flex items-center gap-1 rounded-[6px] px-2 py-1 text-[11px] font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)] disabled:opacity-40"
        >
          <RotateCcw className="h-3 w-3" />
          Reset
        </button>
      </div>
      <div className="min-h-0 flex-1 space-y-0.5 overflow-y-auto p-2">
        {sessions.length === 0 ? (
          <p className="px-2 py-3 text-[12px] text-[var(--text-secondary)]">No sessions yet.</p>
        ) : (
          sessions.map((session) => {
            const active = session.id === activeSessionId
            return (
              <button
                key={session.id}
                type="button"
                disabled={streaming && !active}
                onClick={() => onSelect(session.id)}
                className={cn(
                  'flex w-full flex-col gap-0.5 rounded-[8px] px-2.5 py-2 text-left transition-colors',
                  active
                    ? 'bg-[var(--surface-1)] text-[var(--text-primary)]'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)]',
                  streaming && !active && 'opacity-40',
                )}
              >
                <span className="truncate text-[12px] font-medium">{session.title}</span>
                <span className="text-[10px] text-[var(--text-muted)]">
                  {session.run_count} turn{session.run_count === 1 ? '' : 's'} ·{' '}
                  {new Date(session.created_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                  })}
                </span>
              </button>
            )
          })
        )}
      </div>
    </aside>
  )
}
