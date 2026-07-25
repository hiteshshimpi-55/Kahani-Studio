import { Check, MapPin, Pencil, RefreshCw, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ListingEmptyState,
  ListingShell,
  PageHeader,
} from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { createProject } from '@/features/projects/api/projects-api'
import { cn } from '@/lib/utils'
import { TopicCard } from '../components/TopicCard'
import { useGeolocation } from '../hooks/use-geolocation'
import { useTrendingTopics } from '../hooks/use-trending-topics'
import type { TopicCard as TopicCardType } from '../types'

export function DiscoverPage() {
  const navigate = useNavigate()
  const geo = useGeolocation()

  const [region, setRegion] = useState<string>('IN')
  const [state, setState] = useState<string>('')
  const [editing, setEditing] = useState(false)
  const [editValue, setEditValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  async function handleUse(topic: TopicCardType) {
    const prompt = `Create an original story inspired by this theme: ${topic.title}. ${topic.hook}`
    const project = await createProject({
      name: topic.title,
      description: topic.hook,
    })
    const encodedPrompt = encodeURIComponent(prompt)
    navigate(`/projects/${project.id}/chat?prompt=${encodedPrompt}`)
  }

  useEffect(() => {
    if (geo.location) {
      setRegion(geo.location.country)
      setState(geo.location.state)
    }
  }, [geo.location])

  const locationLabel = state
    ? `${state}, ${geo.location?.country_name ?? region}`
    : (geo.location?.country_name ?? region)

  const { data, loading, error, refresh } = useTrendingTopics(region, state || undefined)

  function openEdit() {
    setEditValue(state || geo.location?.country_name || '')
    setEditing(true)
    setTimeout(() => inputRef.current?.focus(), 0)
  }

  function applyEdit() {
    const trimmed = editValue.trim()
    if (trimmed) {
      const parts = trimmed.split(',').map((s) => s.trim())
      setState(parts[0])
    }
    setEditing(false)
  }

  function cancelEdit() {
    setEditing(false)
  }

  return (
    <ListingShell maxWidth="6xl">
      <PageHeader
        title="Discover"
        description="Hot story topics trending in your area right now. Pick one to start writing."
        actions={
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={refresh}
            disabled={loading || geo.loading}
          >
            <RefreshCw className={cn('h-3.5 w-3.5', loading && 'animate-spin')} />
            Refresh
          </Button>
        }
      >
        {/* Location chip */}
        <div className="mt-4 flex items-center gap-2">
          {geo.loading ? (
            <div className="flex items-center gap-2 rounded-[8px] border border-[var(--folio-border)] bg-[var(--surface-1)] px-3 py-2">
              <div className="h-3.5 w-3.5 animate-pulse rounded-full bg-[var(--text-muted)]" />
              <span className="text-[12px] text-[var(--text-muted)]">Detecting location…</span>
            </div>
          ) : editing ? (
            <div className="flex items-center gap-1.5">
              <div className="flex items-center gap-2 rounded-[8px] border border-[#E6194D] bg-[#E6194D]/5 px-3 py-2">
                <MapPin className="h-3.5 w-3.5 shrink-0 text-[#E6194D]" />
                <input
                  ref={inputRef}
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') applyEdit()
                    if (e.key === 'Escape') cancelEdit()
                  }}
                  placeholder="e.g. Maharashtra, Delhi, Gujarat…"
                  className="w-52 bg-transparent text-[13px] text-[var(--text-primary)] outline-none placeholder:text-[var(--text-muted)]"
                />
              </div>
              <button
                type="button"
                onClick={applyEdit}
                className="flex h-8 w-8 items-center justify-center rounded-[6px] text-green-500 hover:bg-[var(--surface-1)]"
                title="Apply"
              >
                <Check className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={cancelEdit}
                className="flex h-8 w-8 items-center justify-center rounded-[6px] text-[var(--text-muted)] hover:bg-[var(--surface-1)]"
                title="Cancel"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={openEdit}
              className="group flex items-center gap-2 rounded-[8px] border border-[var(--folio-border)] bg-[var(--surface-1)] px-3 py-2 transition-colors hover:border-[var(--folio-border-strong)]"
              title="Change location"
            >
              <MapPin className="h-3.5 w-3.5 shrink-0 text-[#E6194D]" />
              <span className="text-[13px] font-medium text-[var(--text-primary)]">
                {locationLabel}
              </span>
              <Pencil className="h-3 w-3 text-[var(--text-muted)] opacity-0 transition-opacity group-hover:opacity-100" />
            </button>
          )}

          {data && !loading && (
            <span className="text-[11px] text-[var(--text-muted)]">
              {data.topics.length} topics
            </span>
          )}
        </div>
      </PageHeader>

      {loading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="h-64 animate-pulse rounded-[12px] border border-[var(--folio-border)] bg-[var(--surface-1)]"
            />
          ))}
        </div>
      )}

      {error && !loading && (
        <ListingEmptyState
          title="Could not load topics"
          description={error}
          action={
            <Button type="button" variant="secondary" size="sm" onClick={refresh}>
              Try again
            </Button>
          }
        />
      )}

      {data && !loading && data.topics.length === 0 && (
        <ListingEmptyState
          title="No topics found"
          description="Try refreshing or changing the location."
          action={
            <Button type="button" variant="secondary" size="sm" onClick={refresh}>
              Refresh
            </Button>
          }
        />
      )}

      {data && !loading && data.topics.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {data.topics.map((topic) => (
            <TopicCard key={topic.id} topic={topic} onUse={() => handleUse(topic)} />
          ))}
        </div>
      )}
    </ListingShell>
  )
}
