import { useState } from 'react'

import { cn } from '@/lib/utils'

import type { SimulateRequest } from '../types'

interface Props {
  onSubmit: (req: SimulateRequest) => void
  busy: boolean
}

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
      <div className="grid grid-cols-2 gap-3">
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-stone-500">Episode ID</span>
          <input
            className="rounded border border-stone-300 bg-white px-3 py-1.5 text-sm"
            value={episodeId}
            onChange={(e) => setEpisodeId(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-stone-500">Series ID</span>
          <input
            className="rounded border border-stone-300 bg-white px-3 py-1.5 text-sm"
            value={seriesId}
            onChange={(e) => setSeriesId(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-stone-500">Language</span>
          <select
            className="rounded border border-stone-300 bg-white px-3 py-1.5 text-sm"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          >
            <option value="hindi">Hindi</option>
            <option value="english">English</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-stone-500">Genre</span>
          <select
            className="rounded border border-stone-300 bg-white px-3 py-1.5 text-sm"
            value={genre}
            onChange={(e) => setGenre(e.target.value)}
          >
            <option value="thriller">Thriller</option>
            <option value="romance">Romance</option>
            <option value="drama">Drama</option>
            <option value="biopic">Biopic</option>
            <option value="horror">Horror</option>
            <option value="comedy">Comedy</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-stone-500">Title</span>
          <input
            className="rounded border border-stone-300 bg-white px-3 py-1.5 text-sm"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Optional"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-stone-500">Parts</span>
          <input
            type="number"
            min={1}
            max={20}
            className="rounded border border-stone-300 bg-white px-3 py-1.5 text-sm"
            value={partCount}
            onChange={(e) => setPartCount(Number(e.target.value))}
          />
        </label>
      </div>

      <label className="flex flex-col gap-1 text-sm">
        <span className="text-stone-500">Script</span>
        <textarea
          className="h-40 resize-y rounded border border-stone-300 bg-white px-3 py-2 font-mono text-xs"
          value={script}
          onChange={(e) => setScript(e.target.value)}
          placeholder="Paste full episode script here..."
          required
        />
      </label>

      <button
        type="submit"
        disabled={busy || !script.trim()}
        className={cn(
          'self-start rounded bg-stone-900 px-5 py-2 text-sm text-stone-50',
          'disabled:opacity-50',
        )}
      >
        {busy ? 'Starting simulation…' : 'Run audience simulation'}
      </button>
    </form>
  )
}
