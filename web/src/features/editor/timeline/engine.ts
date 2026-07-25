/**
 * Multi-source Web Audio playhead — one buffer / source per clip.
 * Never flattens to a single media element.
 */

export type EngineClip = {
  id: string
  startSec: number
  durationSec: number
  audioUrl?: string
  muted: boolean
  gain?: number
}

export type MultiSourceClockOptions = {
  onTimeUpdate?: (t: number) => void
  onEnded?: () => void
}

export class MultiSourceClock {
  private ctx: AudioContext | null = null
  private master: GainNode | null = null
  private buffers = new Map<string, AudioBuffer>()
  private active: AudioBufferSourceNode[] = []
  private clips: EngineClip[] = []
  private playing = false
  private startedAtCtx = 0
  private playheadAtStart = 0
  private durationSec = 0
  private raf = 0
  private opts: MultiSourceClockOptions

  constructor(opts: MultiSourceClockOptions = {}) {
    this.opts = opts
  }

  get isPlaying(): boolean {
    return this.playing
  }

  getCurrentTime(): number {
    if (!this.playing || !this.ctx) return this.playheadAtStart
    return Math.min(
      this.durationSec,
      this.playheadAtStart + (this.ctx.currentTime - this.startedAtCtx),
    )
  }

  async ensureContext(): Promise<AudioContext> {
    if (!this.ctx) {
      this.ctx = new AudioContext()
      this.master = this.ctx.createGain()
      this.master.connect(this.ctx.destination)
    }
    if (this.ctx.state === 'suspended') await this.ctx.resume()
    return this.ctx
  }

  async loadBuffer(url: string): Promise<AudioBuffer> {
    const cached = this.buffers.get(url)
    if (cached) return cached
    const ctx = await this.ensureContext()
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Failed to load audio ${res.status}`)
    const ab = await res.arrayBuffer()
    const buf = await ctx.decodeAudioData(ab.slice(0))
    this.buffers.set(url, buf)
    return buf
  }

  async preload(clips: EngineClip[]): Promise<void> {
    const urls = [...new Set(clips.map((c) => c.audioUrl).filter(Boolean))] as string[]
    await Promise.all(
      urls.map((u) =>
        this.loadBuffer(u).catch(() => {
          /* skip bad urls */
        }),
      ),
    )
  }

  setClips(clips: EngineClip[], durationSec: number): void {
    this.clips = clips
    this.durationSec = durationSec
  }

  private stopSources(): void {
    for (const s of this.active) {
      try {
        s.stop()
        s.disconnect()
      } catch {
        /* already stopped */
      }
    }
    this.active = []
  }

  private scheduleFrom(playhead: number): void {
    if (!this.ctx || !this.master) return
    this.stopSources()
    const now = this.ctx.currentTime

    for (const clip of this.clips) {
      if (!clip.audioUrl || clip.muted) continue
      const buf = this.buffers.get(clip.audioUrl)
      if (!buf) continue

      const clipEnd = clip.startSec + clip.durationSec
      if (playhead >= clipEnd) continue
      if (playhead + 0.001 > clipEnd) continue

      const offsetInClip = Math.max(0, playhead - clip.startSec)
      const when = now + Math.max(0, clip.startSec - playhead)
      const remain = Math.min(clip.durationSec - offsetInClip, buf.duration - offsetInClip)
      if (remain <= 0.02) continue

      const src = this.ctx.createBufferSource()
      src.buffer = buf
      const g = this.ctx.createGain()
      g.gain.value = clip.gain ?? 1
      src.connect(g)
      g.connect(this.master)
      try {
        src.start(when, offsetInClip, remain)
        this.active.push(src)
      } catch {
        /* ignore */
      }
    }
  }

  private tick = (): void => {
    if (!this.playing) return
    const t = this.getCurrentTime()
    this.opts.onTimeUpdate?.(t)
    if (t >= this.durationSec - 0.02) {
      this.pause()
      this.playheadAtStart = this.durationSec
      this.opts.onTimeUpdate?.(this.durationSec)
      this.opts.onEnded?.()
      return
    }
    this.raf = requestAnimationFrame(this.tick)
  }

  async play(fromSec?: number): Promise<void> {
    await this.ensureContext()
    await this.preload(this.clips)
    if (fromSec !== undefined) this.playheadAtStart = Math.max(0, fromSec)
    this.startedAtCtx = this.ctx!.currentTime
    this.playing = true
    this.scheduleFrom(this.playheadAtStart)
    cancelAnimationFrame(this.raf)
    this.raf = requestAnimationFrame(this.tick)
  }

  pause(): void {
    if (this.playing) {
      this.playheadAtStart = this.getCurrentTime()
    }
    this.playing = false
    this.stopSources()
    cancelAnimationFrame(this.raf)
  }

  seek(sec: number): void {
    const was = this.playing
    this.pause()
    this.playheadAtStart = Math.max(0, Math.min(this.durationSec, sec))
    this.opts.onTimeUpdate?.(this.playheadAtStart)
    if (was) void this.play()
  }

  stop(): void {
    this.pause()
    this.playheadAtStart = 0
    this.opts.onTimeUpdate?.(0)
  }

  dispose(): void {
    this.stop()
    void this.ctx?.close()
    this.ctx = null
    this.master = null
    this.buffers.clear()
  }
}
