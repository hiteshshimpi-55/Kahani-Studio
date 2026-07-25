import {
  addSfxClip,
  findClipByCharacterName,
  findClipByLabel,
  moveClip,
  muteTrackByKind,
} from './ops'
import type { TimelineDoc } from './types'

export type CommandResult = {
  ok: boolean
  message: string
  doc?: TimelineDoc
  /** clip id to regenerate via TTS */
  regenClipId?: string
}

function parseTime(token: string): number | null {
  const t = token.trim().replace(/^at\s+/i, '')
  if (/^\d+:\d{1,2}(\.\d+)?$/.test(t)) {
    const [m, s] = t.split(':')
    return Number(m) * 60 + Number(s)
  }
  if (/^\d+(\.\d+)?s?$/.test(t)) {
    return Number(t.replace(/s$/i, ''))
  }
  return null
}

/**
 * Thin chat-style commands on TimelineDoc.
 * Examples: "mute music", "unmute sfx", "move knock to 0:42", "regen Maya's line", "add sfx door at 12"
 */
export function applyTimelineCommand(doc: TimelineDoc, raw: string): CommandResult {
  const input = raw.trim()
  if (!input) return { ok: false, message: 'Empty command' }
  const lower = input.toLowerCase()

  if (/^(mute|unmute)\s+music\b/.test(lower)) {
    const muted = lower.startsWith('mute')
    return {
      ok: true,
      message: muted ? 'Muted Music lane' : 'Unmuted Music lane',
      doc: muteTrackByKind(doc, 'music', muted),
    }
  }

  if (/^(mute|unmute)\s+sfx\b/.test(lower)) {
    const muted = lower.startsWith('mute')
    return {
      ok: true,
      message: muted ? 'Muted SFX lane' : 'Unmuted SFX lane',
      doc: muteTrackByKind(doc, 'sfx', muted),
    }
  }

  const move = lower.match(/^move\s+(.+?)\s+to\s+(\d+:\d{1,2}(?:\.\d+)?|\d+(?:\.\d+)?s?)\s*$/i)
  if (move) {
    const label = move[1]!.trim()
    const sec = parseTime(move[2]!)
    if (sec == null) return { ok: false, message: 'Could not parse time' }
    const clip =
      findClipByLabel(doc, label, 'sfx') ||
      findClipByLabel(doc, label) ||
      null
    if (!clip) return { ok: false, message: `No clip matching “${label}”` }
    return {
      ok: true,
      message: `Moved “${clip.label}” to ${sec.toFixed(1)}s`,
      doc: moveClip(doc, clip.id, sec),
    }
  }

  const regen = lower.match(/^regen(?:erate)?\s+(.+?)(?:'s)?\s*line\s*$/i)
  if (regen) {
    const name = regen[1]!.replace(/'s$/i, '').trim()
    const clip = findClipByCharacterName(doc, name) || findClipByLabel(doc, name, 'voice')
    if (!clip) return { ok: false, message: `No voice line for “${name}”` }
    return {
      ok: true,
      message: `Regenerating “${clip.label.slice(0, 40)}…”`,
      regenClipId: clip.id,
    }
  }

  const addSfx = lower.match(/^add\s+sfx\s+(.+?)\s+at\s+(\d+:\d{1,2}(?:\.\d+)?|\d+(?:\.\d+)?s?)\s*$/i)
  if (addSfx) {
    const label = addSfx[1]!.trim()
    const sec = parseTime(addSfx[2]!)
    if (sec == null) return { ok: false, message: 'Could not parse time' }
    return {
      ok: true,
      message: `Added SFX “${label}” at ${sec.toFixed(1)}s`,
      doc: addSfxClip(doc, label, sec),
    }
  }

  return {
    ok: false,
    message:
      'Try: mute music · unmute sfx · move knock to 0:42 · regen riya line · add sfx door at 12',
  }
}
