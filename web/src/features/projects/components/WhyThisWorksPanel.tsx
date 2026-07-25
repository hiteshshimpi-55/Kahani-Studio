import { useState } from 'react'

import { analyzeStory } from '../api/projects-api'
import type { ConceptSuggestion, StoryAnalysis } from '../types'

function ConceptCard({ concept }: { concept: ConceptSuggestion }) {
  return (
    <div className="flex flex-col gap-1 rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-0)] px-3 py-3">
      <p className="text-[12px] font-semibold text-[var(--text-primary)] leading-snug">
        {concept.title}
      </p>
      <p className="text-[11px] text-[var(--text-secondary)] leading-snug">{concept.tagline}</p>
      <p className="mt-1 text-[10px] font-medium tracking-wide text-[var(--brand)] uppercase">
        {concept.emotional_hook}
      </p>
    </div>
  )
}

export function WhyThisWorksPanel({
  projectId,
  runId,
  screenplayMd,
}: {
  projectId: string
  runId: string
  screenplayMd: string
}) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState<StoryAnalysis | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleOpen() {
    if (analysis) {
      setOpen((v) => !v)
      return
    }
    setOpen(true)
    setLoading(true)
    setError(null)
    try {
      const result = await analyzeStory(projectId, runId, screenplayMd)
      setAnalysis(result)
    } catch {
      setError('Could not analyse the story. Check that LLM_API_KEY is set.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="border-t border-[var(--folio-border)]">
      <button
        type="button"
        onClick={() => void handleOpen()}
        className="flex w-full items-center gap-2 px-4 py-2.5 text-left hover:bg-[var(--surface-1)] transition-colors"
      >
        <span className="text-[var(--brand)] text-[13px]">✦</span>
        <span className="flex-1 text-[11px] font-semibold tracking-[0.12em] text-[var(--text-secondary)] uppercase">
          Why this story works
        </span>
        <span className="text-[10px] text-[var(--text-muted)]">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="px-4 pb-4">
          {loading && (
            <p className="text-[12px] text-[var(--text-muted)] py-3 animate-pulse">
              Analysing emotional hooks…
            </p>
          )}

          {error && (
            <p className="text-[12px] text-destructive py-2">{error}</p>
          )}

          {analysis && (
            <div className="space-y-4">
              <div>
                <p className="mb-2 text-[10px] font-semibold tracking-[0.14em] text-[var(--text-muted)] uppercase">
                  What makes it work
                </p>
                <ul className="space-y-1.5">
                  {analysis.why_it_works.map((hook, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-[12px] leading-snug text-[var(--text-primary)]"
                    >
                      <span className="mt-0.5 shrink-0 text-[var(--brand)]">·</span>
                      {hook}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <p className="mb-2 text-[10px] font-semibold tracking-[0.14em] text-[var(--text-muted)] uppercase">
                  Similar concepts to explore
                </p>
                <div className="grid grid-cols-3 gap-2">
                  {analysis.concepts.map((concept, i) => (
                    <ConceptCard key={i} concept={concept} />
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
