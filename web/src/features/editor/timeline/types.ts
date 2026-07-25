export type TrackKind = 'voice' | 'music' | 'sfx'

export type ClipStatus = 'placeholder' | 'generating' | 'ready' | 'error'

export interface Clip {
  id: string
  label: string
  text?: string
  startSec: number
  durationSec: number
  audioUrl?: string
  status: ClipStatus
  sourceRef?: string
  sfxKey?: string
  error?: string
}

export interface Track {
  id: string
  kind: TrackKind
  characterId?: string
  name: string
  muted: boolean
  clips: Clip[]
}

export interface TimelineDoc {
  version: 1
  durationSec: number
  tracks: Track[]
  /** characterId → ElevenLabs voice_id */
  voiceMap: Record<string, string>
}

export const DEFAULT_VOICE_MAP: Record<string, string> = {
  narrator: '21m00Tcm4TlvDq8ikWAM', // Rachel
  riya: 'EXAVITQu4vr4xnSDxMaL', // Bella
  arjun: 'pNInz6obpgDQGcFmaJgB', // Adam
  default: '21m00Tcm4TlvDq8ikWAM',
}

export const TRACK_COLORS: Record<string, string> = {
  narrator: '#E6194D',
  music: '#2A6F6F',
  sfx: '#C45C26',
}

const VOICE_PALETTE = ['#3D5A80', '#7B2D8E', '#1B6B4A', '#8B4513', '#4A6FA5', '#6B4C9A']

export function colorForTrack(track: Track, index: number): string {
  if (track.kind === 'music') return TRACK_COLORS.music
  if (track.kind === 'sfx') return TRACK_COLORS.sfx
  if (track.characterId === 'narrator') return TRACK_COLORS.narrator
  return VOICE_PALETTE[index % VOICE_PALETTE.length]!
}
