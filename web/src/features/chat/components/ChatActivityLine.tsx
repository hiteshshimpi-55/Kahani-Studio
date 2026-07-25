import { LoaderCircle } from 'lucide-react'

import { cn } from '@/lib/utils'

import type { ChatActivity } from '../types'

const FALLBACK = 'Working on it…'

type Props = {
  activity?: ChatActivity | null
  className?: string
}

/** Single-line agent status — hides internal graph nodes. */
export function ChatActivityLine({ activity, className }: Props) {
  if (!activity) return null

  return (
    <div
      className={cn(
        'chat-activity-enter mb-2 flex items-center gap-2 text-[13px] text-[var(--text-secondary)]',
        className,
      )}
    >
      <LoaderCircle className="h-3.5 w-3.5 shrink-0 animate-spin text-[var(--brand)]" />
      <span className="italic">{activity.label || FALLBACK}</span>
    </div>
  )
}
