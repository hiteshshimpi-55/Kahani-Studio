import type { Clip, ClipStatus, TimelineDoc, Track } from './types'

function cloneDoc(doc: TimelineDoc): TimelineDoc {
  return structuredClone(doc)
}

function findClip(
  doc: TimelineDoc,
  clipId: string,
): { track: Track; clip: Clip; trackIndex: number; clipIndex: number } | null {
  for (let ti = 0; ti < doc.tracks.length; ti++) {
    const track = doc.tracks[ti]!
    const clipIndex = track.clips.findIndex((c) => c.id === clipId)
    if (clipIndex >= 0) {
      return { track, clip: track.clips[clipIndex]!, trackIndex: ti, clipIndex }
    }
  }
  return null
}

function recalcDuration(doc: TimelineDoc): TimelineDoc {
  let max = 0
  for (const t of doc.tracks) {
    for (const c of t.clips) {
      max = Math.max(max, c.startSec + c.durationSec)
    }
  }
  doc.durationSec = Math.max(doc.durationSec, Math.ceil(max))
  return doc
}

export function moveClip(doc: TimelineDoc, clipId: string, startSec: number): TimelineDoc {
  const next = cloneDoc(doc)
  const found = findClip(next, clipId)
  if (!found) return doc
  found.clip.startSec = Math.max(0, Math.round(startSec * 10) / 10)
  return recalcDuration(next)
}

export function trimClip(
  doc: TimelineDoc,
  clipId: string,
  durationSec: number,
): TimelineDoc {
  const next = cloneDoc(doc)
  const found = findClip(next, clipId)
  if (!found) return doc
  found.clip.durationSec = Math.max(0.3, Math.round(durationSec * 10) / 10)
  return recalcDuration(next)
}

export function muteTrack(doc: TimelineDoc, trackId: string, muted?: boolean): TimelineDoc {
  const next = cloneDoc(doc)
  const track = next.tracks.find((t) => t.id === trackId)
  if (!track) return doc
  track.muted = muted ?? !track.muted
  return next
}

export function muteTrackByKind(
  doc: TimelineDoc,
  kind: Track['kind'],
  muted?: boolean,
): TimelineDoc {
  const next = cloneDoc(doc)
  for (const t of next.tracks) {
    if (t.kind === kind) t.muted = muted ?? !t.muted
  }
  return next
}

export function setClipAudio(
  doc: TimelineDoc,
  clipId: string,
  audioUrl: string | undefined,
  status: ClipStatus = audioUrl ? 'ready' : 'placeholder',
  error?: string,
): TimelineDoc {
  const next = cloneDoc(doc)
  const found = findClip(next, clipId)
  if (!found) return doc
  found.clip.audioUrl = audioUrl
  found.clip.status = status
  found.clip.error = error
  return next
}

export function markClipPending(doc: TimelineDoc, clipId: string): TimelineDoc {
  return setClipAudio(doc, clipId, findClip(doc, clipId)?.clip.audioUrl, 'generating')
}

export function markClipError(doc: TimelineDoc, clipId: string, error: string): TimelineDoc {
  const next = cloneDoc(doc)
  const found = findClip(next, clipId)
  if (!found) return doc
  found.clip.status = 'error'
  found.clip.error = error
  return next
}

export function assignVoice(
  doc: TimelineDoc,
  characterId: string,
  voiceId: string,
): TimelineDoc {
  const next = cloneDoc(doc)
  next.voiceMap = { ...next.voiceMap, [characterId]: voiceId }
  return next
}

export function addSfxClip(
  doc: TimelineDoc,
  label: string,
  startSec: number,
  durationSec = 1.5,
): TimelineDoc {
  const next = cloneDoc(doc)
  let sfx = next.tracks.find((t) => t.kind === 'sfx')
  if (!sfx) {
    sfx = { id: 'track_sfx', kind: 'sfx', name: 'SFX', muted: false, clips: [] }
    next.tracks.push(sfx)
  }
  sfx.clips.push({
    id: `sfx_${Math.random().toString(36).slice(2, 10)}`,
    label,
    startSec: Math.max(0, startSec),
    durationSec,
    status: 'placeholder',
  })
  return recalcDuration(next)
}

export function getVoiceClipsMissingAudio(doc: TimelineDoc): Clip[] {
  const out: Clip[] = []
  for (const t of doc.tracks) {
    if (t.kind !== 'voice') continue
    for (const c of t.clips) {
      if (!c.audioUrl || c.status === 'placeholder' || c.status === 'error') {
        out.push(c)
      }
    }
  }
  return out
}

export function findTrackForClip(doc: TimelineDoc, clipId: string): Track | null {
  return findClip(doc, clipId)?.track ?? null
}

export function findClipByLabel(
  doc: TimelineDoc,
  query: string,
  kind?: Track['kind'],
): Clip | null {
  const q = query.toLowerCase()
  for (const t of doc.tracks) {
    if (kind && t.kind !== kind) continue
    for (const c of t.clips) {
      if (c.label.toLowerCase().includes(q) || (c.text || '').toLowerCase().includes(q)) {
        return c
      }
    }
  }
  return null
}

export function findClipByCharacterName(doc: TimelineDoc, name: string): Clip | null {
  const q = name.toLowerCase()
  for (const t of doc.tracks) {
    if (t.kind !== 'voice') continue
    if (
      (t.name || '').toLowerCase().includes(q) ||
      (t.characterId || '').toLowerCase().includes(q)
    ) {
      const first = t.clips.find((c) => !c.audioUrl || c.status !== 'ready') ?? t.clips[0]
      return first ?? null
    }
  }
  return null
}
