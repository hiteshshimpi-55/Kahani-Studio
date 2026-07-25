import { useState } from 'react'

import { getRunResearch, triggerRunResearch } from '../api/projects-api'
import type { ResearchEntry, StoryResearch } from '../types'

const CATEGORY_LABELS: Record<string, string> = {
  similar_stories: 'Similar Stories',
  cultural_context: 'Cultural Context',
  character_archetypes: 'Character Archetypes',
  emotional_themes: 'Emotional Themes',
}

function SourceCard({ entry }: { entry: ResearchEntry }) {
  return (
    <a
      href={entry.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block rounded-[8px] border border-[var(--folio-border)] bg-[var(--surface-0)] px-3 py-2.5 hover:border-[var(--brand)]/40 transition-colors"
    >
      <p className="text-[11px] font-semibold text-[var(--text-primary)] leading-snug line-clamp-2">
        {entry.title || entry.url}
      </p>
      {entry.snippet && (
        <p className="mt-1 text-[10px] leading-snug text-[var(--text-secondary)] line-clamp-3">
          {entry.snippet}
        </p>
      )}
      <p className="mt-1 text-[9px] text-[var(--text-muted)] truncate">{entry.url}</p>
    </a>
  )
}

function CategorySection({
  label,
  entries,
}: {
  label: string
  entries: ResearchEntry[]
}) {
  if (!entries.length) return null
  return (
    <div className="space-y-1.5">
      <p className="text-[10px] font-semibold tracking-[0.14em] text-[var(--text-muted)] uppercase">
        {label}
      </p>
      <div className="grid grid-cols-2 gap-1.5">
        {entries.slice(0, 4).map((e, i) => (
          <SourceCard key={i} entry={e} />
        ))}
      </div>
    </div>
  )
}

export function StoryResearchPanel({
  projectId,
  runId,
}: {
  projectId: string
  runId: string
}) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [research, setResearch] = useState<StoryResearch | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleOpen() {
    if (!open && !research) {
      setLoading(true)
      setError(null)
      // Try loading cached result first
      try {
        const cached = await getRunResearch(projectId, runId)
        if (cached) {
          setResearch(cached)
          setOpen(true)
          setLoading(false)
          return
        }
      } catch {
        // no cached result — fall through to trigger new search
      }
      // Trigger new research
      try {
        const result = await triggerRunResearch(projectId, runId)
        setResearch(result)
      } catch {
        setError('Research failed. Check that TAVILY_API_KEY is configured.')
      } finally {
        setLoading(false)
      }
    }
    setOpen((v) => !v)
  }

  return (
    <div className="border-t border-[var(--folio-border)]">
      <button
        type="button"
        onClick={() => void handleOpen()}
        className="flex w-full items-center gap-2 px-4 py-2.5 text-left hover:bg-[var(--surface-1)] transition-colors"
      >
        <span className="text-[var(--brand)] text-[13px]">⌖</span>
        <span className="flex-1 text-[11px] font-semibold tracking-[0.12em] text-[var(--text-secondary)] uppercase">
          Story Research
        </span>
        {research && (
          <span className="rounded-full bg-[var(--surface-1)] px-1.5 py-0.5 text-[9px] text-[var(--text-muted)]">
            cached
          </span>
        )}
        <span className="text-[10px] text-[var(--text-muted)]">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-4">
          {loading && (
            <p className="text-[12px] text-[var(--text-muted)] animate-pulse pt-1">
              Searching the web…
            </p>
          )}

          {error && <p className="text-[12px] text-destructive">{error}</p>}

          {research && !loading && (
            <>
              {Object.entries(research.results).map(([cat, entries]) => (
                <CategorySection
                  key={cat}
                  label={CATEGORY_LABELS[cat] ?? cat}
                  entries={entries}
                />
              ))}
              <button
                type="button"
                onClick={() => {
                  setResearch(null)
                  void triggerRunResearch(projectId, runId)
                    .then(setResearch)
                    .catch(() => setError('Refresh failed'))
                }}
                className="text-[10px] text-[var(--text-muted)] hover:text-[var(--brand)] underline"
              >
                Refresh research
              </button>
            </>
          )}
        </div>
      )}
    </div>
  )
}
