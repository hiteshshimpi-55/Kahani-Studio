import { useCallback, useEffect, useRef, useState } from 'react'
import { Pause, Play, Square, Volume2, VolumeX, Wand2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { apiUrl } from '@/lib/api-client'
import { cn } from '@/lib/utils'

import { synthesizeClipsBatch, synthesizeClip } from './api'
import { TimelineCommandBar } from './CommandBar'
import { MultiSourceClock, type EngineClip } from './engine'
import {
  getVoiceClipsMissingAudio,
  markClipError,
  markClipPending,
  muteTrack,
  setClipAudio,
  trimClip,
} from './ops'
import { colorForTrack } from './types'
import type { Clip, TimelineDoc, Track } from './types'

function formatTime(sec: number): string {
  const s = Math.max(0, sec)
  const m = Math.floor(s / 60)
  const r = s - m * 60
  return `${m}:${r.toFixed(1).padStart(4, '0')}`
}

function resolveAudioUrl(url: string | undefined): string | undefined {
  if (!url) return undefined
  if (url.startsWith('http') || url.startsWith('blob:') || url.startsWith('data:')) return url
  return apiUrl(url)
}

type Props = {
  projectId: string
  doc: TimelineDoc
  onChange: (doc: TimelineDoc) => void
  scriptPreview?: string
}

export function TimelineEditor({ projectId, doc, onChange, scriptPreview }: Props) {
  const [playhead, setPlayhead] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [pxPerSec, setPxPerSec] = useState(48)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)
  const [scriptOpen, setScriptOpen] = useState(false)
  const engineRef = useRef<MultiSourceClock | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const clock = new MultiSourceClock({
      onTimeUpdate: (t) => setPlayhead(t),
      onEnded: () => setPlaying(false),
    })
    engineRef.current = clock
    return () => clock.dispose()
  }, [])

  const syncEngine = useCallback(
    (d: TimelineDoc) => {
      const clips: EngineClip[] = []
      for (const track of d.tracks) {
        for (const c of track.clips) {
          clips.push({
            id: c.id,
            startSec: c.startSec,
            durationSec: c.durationSec,
            audioUrl: resolveAudioUrl(c.audioUrl),
            muted: track.muted,
            gain: track.kind === 'music' ? 0.35 : track.kind === 'sfx' ? 0.7 : 1,
          })
        }
      }
      engineRef.current?.setClips(clips, d.durationSec)
    },
    [],
  )

  useEffect(() => {
    syncEngine(doc)
  }, [doc, syncEngine])

  const togglePlay = async () => {
    const eng = engineRef.current
    if (!eng) return
    if (eng.isPlaying) {
      eng.pause()
      setPlaying(false)
      return
    }
    syncEngine(doc)
    await eng.play(playhead >= doc.durationSec - 0.05 ? 0 : playhead)
    setPlaying(true)
  }

  const stop = () => {
    engineRef.current?.stop()
    setPlaying(false)
    setPlayhead(0)
  }

  const seekTo = (sec: number) => {
    engineRef.current?.seek(sec)
    setPlayhead(sec)
  }

  const generateMissing = async () => {
    const missing = getVoiceClipsMissingAudio(doc)
    if (missing.length === 0) {
      setStatusMsg('All voice clips already have audio')
      return
    }
    setBusy(true)
    setStatusMsg(`Generating ${missing.length} voice clip(s)…`)
    let next = doc
    for (const c of missing) {
      next = markClipPending(next, c.id)
    }
    onChange(next)

    const trackOf = (clipId: string): Track | undefined =>
      next.tracks.find((t) => t.clips.some((c) => c.id === clipId))

    const payload = missing
      .map((c) => {
        const track = trackOf(c.id)
        const voiceId =
          (track?.characterId && next.voiceMap[track.characterId]) ||
          next.voiceMap.default ||
          '21m00Tcm4TlvDq8ikWAM'
        return {
          clip_id: c.id,
          text: c.text || c.label,
          voice_id: voiceId,
        }
      })
      .filter((p) => p.text.trim())

    try {
      const { results, errors } = await synthesizeClipsBatch(projectId, payload)
      for (const r of results) {
        next = setClipAudio(next, r.clip_id, r.audio_url, 'ready')
        if (r.duration_hint_sec && r.duration_hint_sec > 0.5) {
          next = trimClip(next, r.clip_id, r.duration_hint_sec)
        }
      }
      for (const e of errors) {
        next = markClipError(next, e.clip_id, e.error)
      }
      onChange(next)
      const stub = results.some((r) => r.stub)
      setStatusMsg(
        stub
          ? `Ready (${results.length}) — using stub tones (set ELEVENLABS_API_KEY for real voices)`
          : `Generated ${results.length} voice clip(s)`,
      )
    } catch (e) {
      setStatusMsg(e instanceof Error ? e.message : 'TTS failed')
    } finally {
      setBusy(false)
    }
  }

  const attachLocalAudio = (file: File) => {
    if (!selectedId) return
    const url = URL.createObjectURL(file)
    onChange(setClipAudio(doc, selectedId, url, 'ready'))
    setStatusMsg(`Attached ${file.name}`)
  }

  const regenClip = async (clipId: string) => {
    let track: Track | undefined
    let clip: Clip | undefined
    for (const t of doc.tracks) {
      const c = t.clips.find((x) => x.id === clipId)
      if (c) {
        track = t
        clip = c
        break
      }
    }
    if (!clip || !track || track.kind !== 'voice') {
      setStatusMsg('Select a voice clip to regenerate')
      return
    }
    setBusy(true)
    let next = markClipPending(doc, clipId)
    onChange(next)
    const voiceId =
      (track.characterId && next.voiceMap[track.characterId]) ||
      next.voiceMap.default ||
      '21m00Tcm4TlvDq8ikWAM'
    try {
      const r = await synthesizeClip(projectId, {
        clip_id: clipId,
        text: clip.text || clip.label,
        voice_id: voiceId,
      })
      next = setClipAudio(next, clipId, r.audio_url, 'ready')
      if (r.duration_hint_sec) next = trimClip(next, clipId, r.duration_hint_sec)
      onChange(next)
      setStatusMsg(r.stub ? 'Regenerated (stub tone)' : 'Line regenerated')
    } catch (e) {
      onChange(markClipError(next, clipId, e instanceof Error ? e.message : 'error'))
      setStatusMsg(e instanceof Error ? e.message : 'Regen failed')
    } finally {
      setBusy(false)
    }
  }

  const width = Math.max(640, doc.durationSec * pxPerSec + 120)

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <Button type="button" size="sm" onClick={() => void togglePlay()} disabled={busy}>
          {playing ? <Pause className="size-3.5" /> : <Play className="size-3.5" />}
          {playing ? 'Pause' : 'Play'}
        </Button>
        <Button type="button" size="sm" variant="secondary" onClick={stop}>
          <Square className="size-3.5" />
          Stop
        </Button>
        <span className="font-mono text-[12px] text-[var(--text-secondary)] tabular-nums">
          {formatTime(playhead)} / {formatTime(doc.durationSec)}
        </span>
        <label className="ml-2 flex items-center gap-1.5 text-[12px] text-[var(--text-secondary)]">
          Zoom
          <input
            type="range"
            min={24}
            max={120}
            value={pxPerSec}
            onChange={(e) => setPxPerSec(Number(e.target.value))}
            className="w-24"
          />
        </label>
        <div className="flex-1" />
        <Button
          type="button"
          size="sm"
          variant="secondary"
          disabled={busy}
          onClick={() => void generateMissing()}
        >
          <Wand2 className="size-3.5" />
          Generate voices
        </Button>
        <Button
          type="button"
          size="sm"
          variant="secondary"
          disabled={busy || !selectedId}
          onClick={() => selectedId && void regenClip(selectedId)}
        >
          Regen line
        </Button>
        <label className="inline-flex h-8 cursor-pointer items-center gap-1.5 rounded-[6px] bg-[var(--surface-1)] px-3 text-[12px] font-medium hover:bg-[var(--surface-0)]">
          Attach audio
          <input
            type="file"
            accept="audio/*"
            className="hidden"
            disabled={!selectedId}
            onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) attachLocalAudio(f)
              e.target.value = ''
            }}
          />
        </label>
        {scriptPreview ? (
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={() => setScriptOpen((o) => !o)}
          >
            {scriptOpen ? 'Hide script' : 'Script'}
          </Button>
        ) : null}
      </div>

      {statusMsg ? (
        <p className="text-[12px] text-[var(--text-secondary)]">{statusMsg}</p>
      ) : null}

      <div
        ref={scrollRef}
        className="overflow-x-auto rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-0)]"
      >
        <div className="relative min-w-full" style={{ width }}>
          {/* ruler */}
          <div className="sticky top-0 z-10 flex h-7 border-b border-[var(--folio-border)] bg-[var(--surface-1)]">
            <div className="w-36 shrink-0 border-r border-[var(--folio-border)] px-2 text-[10px] leading-7 text-[var(--text-secondary)]">
              Lane
            </div>
            <div
              className="relative flex-1 cursor-pointer"
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect()
                const x = e.clientX - rect.left + (scrollRef.current?.scrollLeft ?? 0)
                seekTo(Math.max(0, x / pxPerSec))
              }}
            >
              {Array.from({ length: Math.ceil(doc.durationSec) + 1 }, (_, i) => (
                <span
                  key={i}
                  className="absolute top-0 text-[10px] text-[var(--text-secondary)]"
                  style={{ left: i * pxPerSec }}
                >
                  {i % 5 === 0 ? formatTime(i).replace(/\.0$/, '') : ''}
                </span>
              ))}
            </div>
          </div>

          {doc.tracks.map((track, ti) => (
            <LaneRow
              key={track.id}
              track={track}
              color={colorForTrack(track, ti)}
              pxPerSec={pxPerSec}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onMute={() => onChange(muteTrack(doc, track.id))}
            />
          ))}

          {/* playhead */}
          <div
            className="pointer-events-none absolute top-0 bottom-0 z-20 w-px bg-[var(--brand)]"
            style={{ left: 144 + playhead * pxPerSec }}
          />
        </div>
      </div>

      <TimelineCommandBar
        doc={doc}
        onChange={onChange}
        onRegen={(id) => void regenClip(id)}
      />

      {scriptOpen && scriptPreview ? (
        <pre className="max-h-64 overflow-auto rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-0)] p-4 font-sans text-[13px] leading-6 whitespace-pre-wrap text-[var(--text-primary)]">
          {scriptPreview}
        </pre>
      ) : null}
    </div>
  )
}

function LaneRow({
  track,
  color,
  pxPerSec,
  selectedId,
  onSelect,
  onMute,
}: {
  track: Track
  color: string
  pxPerSec: number
  selectedId: string | null
  onSelect: (id: string) => void
  onMute: () => void
}) {
  return (
    <div className="flex min-h-[52px] border-b border-[var(--folio-border)] last:border-b-0">
      <div className="flex w-36 shrink-0 items-center gap-1.5 border-r border-[var(--folio-border)] px-2">
        <span
          className="size-2 shrink-0 rounded-full"
          style={{ background: color, opacity: track.muted ? 0.35 : 1 }}
        />
        <span
          className={cn(
            'truncate text-[11px] font-medium',
            track.muted && 'text-[var(--text-secondary)] line-through',
          )}
          title={track.name}
        >
          {track.name}
        </span>
        <button
          type="button"
          className="ml-auto text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          onClick={onMute}
          title={track.muted ? 'Unmute' : 'Mute'}
        >
          {track.muted ? <VolumeX className="size-3.5" /> : <Volume2 className="size-3.5" />}
        </button>
      </div>
      <div className="relative flex-1 py-1.5">
        {track.clips.map((clip) => (
          <ClipBlock
            key={clip.id}
            clip={clip}
            color={color}
            pxPerSec={pxPerSec}
            muted={track.muted}
            selected={selectedId === clip.id}
            onSelect={() => onSelect(clip.id)}
          />
        ))}
      </div>
    </div>
  )
}

function ClipBlock({
  clip,
  color,
  pxPerSec,
  muted,
  selected,
  onSelect,
}: {
  clip: Clip
  color: string
  pxPerSec: number
  muted: boolean
  selected: boolean
  onSelect: () => void
}) {
  const w = Math.max(8, clip.durationSec * pxPerSec - 2)
  return (
    <button
      type="button"
      onClick={onSelect}
      title={`${clip.label}${clip.text ? `\n${clip.text}` : ''}\n${clip.status}`}
      className={cn(
        'absolute top-1.5 h-9 overflow-hidden rounded-[4px] px-1.5 text-left text-[10px] leading-tight text-white transition-shadow',
        selected && 'ring-2 ring-[var(--brand)] ring-offset-1',
        muted && 'opacity-40',
      )}
      style={{
        left: clip.startSec * pxPerSec,
        width: w,
        background: color,
        opacity: muted ? 0.35 : clip.status === 'placeholder' ? 0.55 : 0.92,
      }}
    >
      <span className="block truncate font-medium">{clip.label}</span>
      <span className="block truncate opacity-80">
        {clip.status === 'generating'
          ? '…'
          : clip.status === 'ready'
            ? 'ready'
            : clip.status === 'error'
              ? 'error'
              : 'pending'}
      </span>
    </button>
  )
}
