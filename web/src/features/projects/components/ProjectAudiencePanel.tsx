import { useEffect, useRef, useState } from 'react'

import type { SimRun } from '@/features/audience/types'

import { getProjectAudienceSimLatest, triggerProjectAudienceSim } from '../api/projects-api'

const GENRES = ['thriller', 'romance', 'drama', 'biopic', 'horror', 'comedy']
const LANGUAGES = ['hindi', 'english']

function ScoreBar({ label, score }: { label: string; score: number }) {
  const pct = Math.round(score * 100)
  const color =
    score >= 0.7 ? 'bg-emerald-500' : score >= 0.5 ? 'bg-amber-400' : 'bg-rose-500'
  return (
    <div className="flex items-center gap-2">
      <span className="w-24 shrink-0 text-[11px] text-[var(--text-secondary)]">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-[var(--folio-border)]">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-[11px] font-medium text-[var(--text-primary)]">
        {pct}%
      </span>
    </div>
  )
}

export function ProjectAudiencePanel({ projectId }: { projectId: string }) {
  const [open, setOpen] = useState(false)
  const [genre, setGenre] = useState('thriller')
  const [language, setLanguage] = useState('hindi')
  const [simRun, setSimRun] = useState<SimRun | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  function startPolling() {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      const run = (await getProjectAudienceSimLatest(projectId)) as SimRun | null
      if (!run) return
      setSimRun(run)
      if (run.status === 'COMPLETED' || run.status === 'FAILED') {
        clearInterval(pollRef.current!)
        pollRef.current = null
        setBusy(false)
      }
    }, 2000)
  }

  async function handleRun() {
    setBusy(true)
    setError(null)
    setSimRun(null)
    try {
      await triggerProjectAudienceSim(projectId, { genre, language, part_count: 5 })
      startPolling()
    } catch {
      setError('Failed to trigger analysis. Check that a script has been generated.')
      setBusy(false)
    }
  }

  async function handleOpen() {
    if (!open) {
      // Try to load the latest result immediately on first open
      const existing = (await getProjectAudienceSimLatest(projectId)) as SimRun | null
      if (existing) setSimRun(existing)
      if (existing?.status === 'PENDING' || existing?.status === 'RUNNING') {
        setBusy(true)
        startPolling()
      }
    }
    setOpen((v) => !v)
  }

  const isRunning = simRun?.status === 'PENDING' || simRun?.status === 'RUNNING'
  const audit = simRun?.audit

  return (
    <div className="border-t border-[var(--folio-border)]">
      <button
        type="button"
        onClick={() => void handleOpen()}
        className="flex w-full items-center gap-2 px-4 py-2.5 text-left hover:bg-[var(--surface-1)] transition-colors"
      >
        <span className="text-[var(--brand)] text-[13px]">◎</span>
        <span className="flex-1 text-[11px] font-semibold tracking-[0.12em] text-[var(--text-secondary)] uppercase">
          Audience Analytics
        </span>
        <span className="text-[10px] text-[var(--text-muted)]">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3">
          {/* Controls */}
          {!isRunning && (
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <select
                value={genre}
                onChange={(e) => setGenre(e.target.value)}
                className="rounded-[6px] border border-[var(--folio-border)] bg-[var(--surface-0)] px-2 py-1 text-[11px] text-[var(--text-primary)] outline-none"
              >
                {GENRES.map((g) => (
                  <option key={g} value={g}>
                    {g}
                  </option>
                ))}
              </select>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="rounded-[6px] border border-[var(--folio-border)] bg-[var(--surface-0)] px-2 py-1 text-[11px] text-[var(--text-primary)] outline-none"
              >
                {LANGUAGES.map((l) => (
                  <option key={l} value={l}>
                    {l}
                  </option>
                ))}
              </select>
              <button
                type="button"
                disabled={busy}
                onClick={() => void handleRun()}
                className="rounded-[6px] bg-[var(--brand)] px-3 py-1 text-[11px] font-medium text-white disabled:opacity-50"
              >
                {busy ? 'Queuing…' : simRun ? 'Re-run' : 'Run Analysis'}
              </button>
            </div>
          )}

          {error && <p className="text-[12px] text-destructive">{error}</p>}

          {isRunning && (
            <p className="text-[12px] text-[var(--text-muted)] animate-pulse">
              Simulating 24 personas…
            </p>
          )}

          {simRun?.status === 'FAILED' && (
            <p className="text-[12px] text-destructive">
              Simulation failed: {simRun.error ?? 'unknown error'}
            </p>
          )}

          {simRun?.status === 'COMPLETED' && audit && (
            <div className="space-y-3">
              {/* Overall score chip */}
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-semibold tracking-[0.14em] text-[var(--text-muted)] uppercase">
                  Overall
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${
                    audit.overall_score >= 0.7
                      ? 'bg-emerald-100 text-emerald-700'
                      : audit.overall_score >= 0.5
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-rose-100 text-rose-700'
                  }`}
                >
                  {Math.round(audit.overall_score * 100)}%
                </span>
                <span className="text-[10px] text-[var(--text-muted)]">
                  {simRun.persona_count} personas · UNCALIBRATED
                </span>
              </div>

              <div className="space-y-1.5">
                <ScoreBar label="Hook" score={audit.hook_score.score} />
                <ScoreBar label="Pacing" score={audit.pacing_score.score} />
                <ScoreBar label="Dialogue" score={audit.dialogue_score.score} />
                <ScoreBar label="Cliffhanger" score={audit.cliffhanger_score.score} />
              </div>

              {simRun.patches.length > 0 && (
                <p className="text-[11px] text-[var(--text-muted)]">
                  {simRun.patches.length} patch suggestion
                  {simRun.patches.length !== 1 ? 's' : ''} —{' '}
                  <a
                    href="/audience"
                    className="text-[var(--brand)] hover:underline"
                  >
                    view full report →
                  </a>
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
