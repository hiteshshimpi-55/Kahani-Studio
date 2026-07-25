import { ArrowRight, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { TopicCard as TopicCardType } from '../types'

const GENRE_COLORS: Record<string, string> = {
  Thriller: 'bg-red-500/10 text-red-400',
  Romance: 'bg-pink-500/10 text-pink-400',
  Drama: 'bg-violet-500/10 text-violet-400',
  Horror: 'bg-orange-500/10 text-orange-400',
  Comedy: 'bg-yellow-500/10 text-yellow-500',
  Family: 'bg-green-500/10 text-green-400',
  Crime: 'bg-rose-500/10 text-rose-400',
  Mystery: 'bg-indigo-500/10 text-indigo-400',
  Spiritual: 'bg-amber-500/10 text-amber-400',
  Historical: 'bg-stone-500/10 text-stone-400',
}

type Props = {
  topic: TopicCardType
  onUse: () => Promise<void>
}

export function TopicCard({ topic, onUse }: Props) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const genreColor =
    GENRE_COLORS[topic.genre] ?? 'bg-[var(--surface-1)] text-[var(--text-secondary)]'

  async function handleUse() {
    setBusy(true)
    setErr(null)
    try {
      await onUse()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to create project')
      setBusy(false)
    }
  }

  return (
    <div className="group flex flex-col gap-3 rounded-[12px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-5 transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <span
          className={cn(
            'inline-flex shrink-0 items-center rounded-[5px] px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide',
            genreColor,
          )}
        >
          {topic.genre}
        </span>
        <span className="text-[11px] text-[var(--text-muted)] italic">{topic.mood}</span>
      </div>

      <div className="flex-1 space-y-2">
        <h3 className="text-[15px] font-semibold leading-snug text-[var(--text-primary)]">
          {topic.title}
        </h3>
        <p className="text-[13px] leading-relaxed text-[var(--text-secondary)]">{topic.hook}</p>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {topic.tags.map((tag) => (
          <span
            key={tag}
            className="rounded-[4px] bg-[var(--surface-1)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-secondary)]"
          >
            {tag}
          </span>
        ))}
      </div>

      <p className="border-t border-[var(--folio-border)] pt-3 text-[11px] leading-relaxed text-[var(--text-muted)]">
        {topic.why_trending}
      </p>

      {err && <p className="text-[11px] text-destructive">{err}</p>}

      <Button
        type="button"
        variant="secondary"
        size="sm"
        className="mt-1 w-full justify-between"
        onClick={() => void handleUse()}
        disabled={busy}
      >
        {busy ? (
          <>
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Creating project…
          </>
        ) : (
          <>
            Start with this
            <ArrowRight className="h-3.5 w-3.5" />
          </>
        )}
      </Button>
    </div>
  )
}
