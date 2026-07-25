import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'

import type { SimulateRequest } from '../types'

interface Props {
  onSubmit: (req: SimulateRequest) => void
  busy: boolean
}

const fieldClass =
  'flex h-9 w-full rounded-[6px] border border-[var(--folio-border)] bg-[var(--surface-0)] px-3 py-2 text-[13px] text-[var(--text-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--folio-border-strong)]'

export function SimulateForm({ onSubmit, busy }: Props) {
  const [episodeId, setEpisodeId] = useState('ep-001')
  const [seriesId, setSeriesId] = useState('series-001')
  const [title, setTitle] = useState('')
  const [language, setLanguage] = useState('hindi')
  const [genre, setGenre] = useState('thriller')
  const [partCount, setPartCount] = useState(5)
  const [script, setScript] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!script.trim()) return
    onSubmit({
      episode_id: episodeId,
      series_id: seriesId,
      title,
      language,
      genre,
      part_count: partCount,
      script,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <label className="flex flex-col gap-1.5 text-[13px]">
          <span className="text-[11px] font-semibold tracking-[0.12em] text-[var(--text-muted)] uppercase">
            Episode ID
          </span>
          <Input value={episodeId} onChange={(e) => setEpisodeId(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5 text-[13px]">
          <span className="text-[11px] font-semibold tracking-[0.12em] text-[var(--text-muted)] uppercase">
            Series ID
          </span>
          <Input value={seriesId} onChange={(e) => setSeriesId(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5 text-[13px]">
          <span className="text-[11px] font-semibold tracking-[0.12em] text-[var(--text-muted)] uppercase">
            Language
          </span>
          <select
            className={fieldClass}
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          >
            <option value="hindi">Hindi</option>
            <option value="english">English</option>
          </select>
        </label>
        <label className="flex flex-col gap-1.5 text-[13px]">
          <span className="text-[11px] font-semibold tracking-[0.12em] text-[var(--text-muted)] uppercase">
            Genre
          </span>
          <select className={fieldClass} value={genre} onChange={(e) => setGenre(e.target.value)}>
            <option value="thriller">Thriller</option>
            <option value="romance">Romance</option>
            <option value="drama">Drama</option>
            <option value="biopic">Biopic</option>
            <option value="horror">Horror</option>
            <option value="comedy">Comedy</option>
          </select>
        </label>
        <label className="flex flex-col gap-1.5 text-[13px]">
          <span className="text-[11px] font-semibold tracking-[0.12em] text-[var(--text-muted)] uppercase">
            Title
          </span>
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Optional"
          />
        </label>
        <label className="flex flex-col gap-1.5 text-[13px]">
          <span className="text-[11px] font-semibold tracking-[0.12em] text-[var(--text-muted)] uppercase">
            Parts
          </span>
          <Input
            type="number"
            min={1}
            max={20}
            value={partCount}
            onChange={(e) => setPartCount(Number(e.target.value))}
          />
        </label>
      </div>

      <label className="flex flex-col gap-1.5 text-[13px]">
        <span className="text-[11px] font-semibold tracking-[0.12em] text-[var(--text-muted)] uppercase">
          Script
        </span>
        <Textarea
          className="h-40 resize-y font-mono text-[12px]"
          value={script}
          onChange={(e) => setScript(e.target.value)}
          placeholder="Paste full episode script here…"
          required
        />
      </label>

      <Button type="submit" disabled={busy || !script.trim()} className="self-start">
        {busy ? 'Starting simulation…' : 'Run audience simulation'}
      </Button>
    </form>
  )
}
