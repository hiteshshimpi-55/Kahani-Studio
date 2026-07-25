import { useMemo, useState } from 'react'
import { LoaderCircle, Play } from 'lucide-react'

import { ListingShell, PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

import { PersonaGraph } from './PersonaGraph'

/** Mock selectors only — no API calls yet */
const MOCK_PROJECTS = [
  { id: 'proj-midnight', name: 'Midnight House' },
  { id: 'proj-ledger', name: 'Blood Ledger' },
  { id: 'proj-witness', name: 'The Midnight Witness' },
] as const

const MOCK_DRAFTS: Record<string, Array<{ id: string; label: string }>> = {
  'proj-midnight': [
    { id: 'd1', label: 'Ep 1 — The Knock' },
    { id: 'd2', label: 'Ep 2 — Locked Room' },
    { id: 'd3', label: 'Ep 3 — Last Signal' },
  ],
  'proj-ledger': [
    { id: 'd4', label: 'Ep 1 — Hidden Row' },
    { id: 'd5', label: 'Ep 2 — Manager’s Smile' },
  ],
  'proj-witness': [
    { id: 'd6', label: 'Ep 1 — Night Fare' },
    { id: 'd7', label: 'Ep 2 — Rear Mirror' },
  ],
}

const selectClass =
  'h-9 w-full min-w-[180px] rounded-[6px] border border-[var(--folio-border)] bg-[var(--surface-0)] px-3 text-[13px] text-[var(--text-primary)] outline-none focus-visible:ring-2 focus-visible:ring-[var(--folio-border-strong)]'

export function AudienceSimView() {
  const [projectId, setProjectId] = useState<string>(MOCK_PROJECTS[0].id)
  const [draftId, setDraftId] = useState<string>(MOCK_DRAFTS[MOCK_PROJECTS[0].id][0].id)
  const [running, setRunning] = useState(false)
  const [ranOnce, setRanOnce] = useState(false)

  const drafts = useMemo(() => MOCK_DRAFTS[projectId] ?? [], [projectId])

  const handleProjectChange = (next: string) => {
    setProjectId(next)
    const first = MOCK_DRAFTS[next]?.[0]
    setDraftId(first?.id ?? '')
    setRanOnce(false)
    setRunning(false)
  }

  const canRun = Boolean(projectId && draftId) && !running

  const handleRun = () => {
    if (!canRun) return
    setRunning(true)
    setRanOnce(true)
    // UI-only: fake a short “simulating” pulse, no API
    window.setTimeout(() => setRunning(false), 2200)
  }

  return (
    <ListingShell maxWidth="5xl" className="px-6 py-8 md:px-8">
      <PageHeader
        title="Audience simulation"
        description="Watch an uncalibrated persona cohort react to a draft. Hover nodes to inspect listeners."
      />

      <section className="mb-5 flex flex-col gap-3 rounded-[12px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-4 shadow-[var(--shadow-card)] sm:flex-row sm:flex-wrap sm:items-end">
        <label className="flex min-w-[200px] flex-1 flex-col gap-1.5">
          <span className="text-[11px] font-semibold tracking-[0.12em] text-[var(--text-muted)] uppercase">
            Project
          </span>
          <select
            className={selectClass}
            value={projectId}
            onChange={(e) => handleProjectChange(e.target.value)}
          >
            {MOCK_PROJECTS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>

        <label className="flex min-w-[220px] flex-1 flex-col gap-1.5">
          <span className="text-[11px] font-semibold tracking-[0.12em] text-[var(--text-muted)] uppercase">
            Draft
          </span>
          <select
            className={selectClass}
            value={draftId}
            onChange={(e) => {
              setDraftId(e.target.value)
              setRanOnce(false)
              setRunning(false)
            }}
            disabled={!drafts.length}
          >
            {drafts.map((d) => (
              <option key={d.id} value={d.id}>
                {d.label}
              </option>
            ))}
          </select>
        </label>

        <Button
          type="button"
          disabled={!canRun}
          onClick={handleRun}
          className={cn('h-9 shrink-0 gap-2 px-5', running && 'opacity-90')}
        >
          {running ? (
            <>
              <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
              Simulating…
            </>
          ) : (
            <>
              <Play className="h-3.5 w-3.5 fill-current" />
              Run simulation
            </>
          )}
        </Button>
      </section>

      <PersonaGraph active={running || ranOnce} />

      <p className="mt-3 text-[12px] text-[var(--text-muted)]">
        {running
          ? 'Persona cohort is listening… (UI preview — no API yet)'
          : ranOnce
            ? 'Preview complete. Wire this to the audience sim API when ready.'
            : 'Select a project and draft, then run the simulation.'}
      </p>
    </ListingShell>
  )
}
