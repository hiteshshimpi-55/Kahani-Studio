import { DEFAULT_VOICE_MAP, type Clip, type TimelineDoc, type Track } from './types'

type BibleChar = { id?: string; name?: string; role?: string }
type Part = {
  part_number?: number
  title?: string
  screenplay?: string
  text?: string
  sfx_cues?: string[]
  target_duration_sec?: number
}

function slugId(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '')
    .slice(0, 40)
}

function estimateDurationSec(text: string): number {
  const words = text.trim().split(/\s+/).filter(Boolean).length
  return Math.max(1.2, Math.round((words / 2.6) * 10) / 10)
}

function uid(prefix: string): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`
}

/** SPEAKER: [direction] dialogue */
const LINE_RE = /^([A-Z][A-Z0-9 _'-]{0,40}):\s*(?:\[([^\]]*)\]\s*)?(.*)$/

/** [SFX: knock] or [SFX knock] */
const SFX_INLINE_RE = /\[SFX[:\s]+([^\]]+)\]/gi

function parseScreenplay(screenplay: string): {
  dialogue: { speaker: string; direction?: string; text: string }[]
  inlineSfx: string[]
} {
  const dialogue: { speaker: string; direction?: string; text: string }[] = []
  const inlineSfx: string[] = []
  for (const raw of screenplay.split(/\n+/)) {
    const line = raw.trim()
    if (!line) continue
    for (const m of line.matchAll(SFX_INLINE_RE)) {
      if (m[1]) inlineSfx.push(m[1].trim())
    }
    const cleaned = line.replace(SFX_INLINE_RE, '').trim()
    if (!cleaned) continue
    const m = LINE_RE.exec(cleaned)
    if (m) {
      const text = (m[3] ?? '').trim()
      if (text) {
        dialogue.push({
          speaker: (m[1] ?? '').trim(),
          direction: m[2]?.trim(),
          text,
        })
      }
    }
  }
  return { dialogue, inlineSfx }
}

function ensureVoiceTrack(
  tracks: Map<string, Track>,
  characterId: string,
  name: string,
): Track {
  let t = tracks.get(characterId)
  if (!t) {
    t = {
      id: `track_voice_${characterId}`,
      kind: 'voice',
      characterId,
      name,
      muted: false,
      clips: [],
    }
    tracks.set(characterId, t)
  }
  return t
}

/**
 * Seed a multi-lane timeline from a Script Writer package
 * (bible.characters + parts[].screenplay + sfx_cues).
 */
export function buildTimelineFromScript(
  pkg: Record<string, unknown> | null | undefined,
): TimelineDoc {
  const bible = (pkg?.bible as { characters?: BibleChar[] } | undefined) ?? {}
  const chars = Array.isArray(bible.characters) ? bible.characters : []
  const parts = (Array.isArray(pkg?.parts) ? pkg!.parts : []) as Part[]

  const voiceMap: Record<string, string> = { ...DEFAULT_VOICE_MAP }
  const voiceTracks = new Map<string, Track>()

  // Always ensure narrator lane
  ensureVoiceTrack(voiceTracks, 'narrator', 'Narrator')

  for (const c of chars) {
    const name = (c.name || c.id || 'Character').trim()
    const id = (c.id || slugId(name) || 'character').toLowerCase()
    ensureVoiceTrack(voiceTracks, id, name.replace(/_/g, ' '))
    if (!voiceMap[id]) {
      voiceMap[id] = DEFAULT_VOICE_MAP.default!
    }
  }

  const sfxTrack: Track = {
    id: 'track_sfx',
    kind: 'sfx',
    name: 'SFX',
    muted: false,
    clips: [],
  }
  const musicTrack: Track = {
    id: 'track_music',
    kind: 'music',
    name: 'Music',
    muted: false,
    clips: [],
  }

  let cursor = 0
  let partGap = 0.4

  for (const part of parts) {
    const screenplay = String(part.screenplay || part.text || '')
    const { dialogue, inlineSfx } = parseScreenplay(screenplay)

    for (const line of dialogue) {
      const characterId = slugId(line.speaker) || 'narrator'
      const display =
        chars.find((c) => (c.id || '').toLowerCase() === characterId)?.name ||
        line.speaker
      const track = ensureVoiceTrack(voiceTracks, characterId, display)
      if (!voiceMap[characterId]) {
        voiceMap[characterId] = DEFAULT_VOICE_MAP.default!
      }
      const durationSec = estimateDurationSec(line.text)
      const clip: Clip = {
        id: uid('clip'),
        label: line.text.slice(0, 48) + (line.text.length > 48 ? '…' : ''),
        text: line.text,
        startSec: Math.round(cursor * 10) / 10,
        durationSec,
        status: 'placeholder',
        sourceRef: part.title ? `part:${part.part_number}` : undefined,
      }
      track.clips.push(clip)
      cursor += durationSec + 0.15
    }

    const cues = [
      ...(Array.isArray(part.sfx_cues) ? part.sfx_cues : []),
      ...inlineSfx,
    ]
    for (const cue of cues) {
      const label = String(cue).trim()
      if (!label) continue
      sfxTrack.clips.push({
        id: uid('sfx'),
        label,
        startSec: Math.max(0, Math.round((cursor - 1.2) * 10) / 10),
        durationSec: 1.5,
        status: 'placeholder',
        sfxKey: slugId(label),
      })
    }

    cursor += partGap
  }

  // Music bed spanning full episode (placeholder)
  const durationSec = Math.max(
    cursor,
    typeof pkg?.total_duration_sec === 'number' ? Number(pkg.total_duration_sec) : 0,
    8,
  )
  musicTrack.clips.push({
    id: uid('music'),
    label: 'Score bed',
    startSec: 0,
    durationSec: Math.min(durationSec, Math.max(durationSec * 0.85, 12)),
    status: 'placeholder',
  })

  // Order: narrator first, then other voices, then music, sfx
  const orderedVoices = [...voiceTracks.values()].sort((a, b) => {
    if (a.characterId === 'narrator') return -1
    if (b.characterId === 'narrator') return 1
    return (a.name || '').localeCompare(b.name || '')
  })

  return {
    version: 1,
    durationSec: Math.ceil(durationSec),
    tracks: [...orderedVoices, musicTrack, sfxTrack],
    voiceMap,
  }
}
