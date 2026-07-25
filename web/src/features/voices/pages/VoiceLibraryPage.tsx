import { useState } from 'react'
import { Play } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

/** Library cards; elevenLabsVoiceId maps into Editor timeline voiceMap. */
const VOICES = [
  {
    id: 'n1',
    name: 'NARRATOR Calm',
    lang: 'English',
    style: 'Thriller guide',
    tags: ['narrator'],
    elevenLabsVoiceId: '21m00Tcm4TlvDq8ikWAM',
    characterHint: 'narrator',
  },
  {
    id: 'r1',
    name: 'RIYA Soft',
    lang: 'Hindi',
    style: 'Nervous lead',
    tags: ['character'],
    elevenLabsVoiceId: 'EXAVITQu4vr4xnSDxMaL',
    characterHint: 'riya',
  },
  {
    id: 'a1',
    name: 'ARJUN Steady',
    lang: 'Hindi',
    style: 'Ally / protector',
    tags: ['character'],
    elevenLabsVoiceId: 'pNInz6obpgDQGcFmaJgB',
    characterHint: 'arjun',
  },
  {
    id: 'v1',
    name: 'THE VOICE',
    lang: 'English',
    style: 'Distorted whisper',
    tags: ['fx-voice'],
    elevenLabsVoiceId: 'VR6AewLTigWG4xSOukaG',
  },
  {
    id: 'h1',
    name: 'HOST Warm',
    lang: 'English',
    style: 'Podcast energy',
    tags: ['narrator'],
    elevenLabsVoiceId: '21m00Tcm4TlvDq8ikWAM',
  },
]

const SFX = [
  { id: 's1', name: 'Door creak', category: 'Foley', tags: ['interior'] },
  { id: 's2', name: 'Distant thunder', category: 'Ambience', tags: ['weather'] },
  { id: 's3', name: 'Footsteps wood', category: 'Foley', tags: ['movement'] },
  { id: 's4', name: 'Heartbeat low', category: 'Tension', tags: ['score-bed'] },
  { id: 's5', name: 'City night bed', category: 'Ambience', tags: ['exterior'] },
  { id: 's6', name: 'Radio static sting', category: 'Transition', tags: ['sting'] },
]

type Tab = 'voices' | 'sfx'

export function VoiceLibraryPage() {
  const [tab, setTab] = useState<Tab>('voices')

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="text-[22px] font-semibold tracking-tight">Voice & SFX</h1>
      <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
        Global library of real-world casting voices and sound effects. Preview is demo-only for now.
      </p>

      <div className="mt-6 flex gap-1 rounded-[8px] bg-[var(--surface-1)] p-1 w-fit">
        {(
          [
            { id: 'voices', label: 'Voices' },
            { id: 'sfx', label: 'Sound effects' },
          ] as const
        ).map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={cn(
              'rounded-[6px] px-3 py-1.5 text-[12px] font-medium transition-colors',
              tab === t.id
                ? 'bg-[var(--surface-2)] text-[var(--text-primary)] shadow-sm'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]',
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'voices' ? (
        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {VOICES.map((v) => (
            <div
              key={v.id}
              className="rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[14px] font-semibold">{v.name}</p>
                  <p className="mt-1 text-[12px] text-[var(--text-secondary)]">
                    {v.lang} · {v.style}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {v.tags.map((tag) => (
                      <span
                        key={tag}
                        className="rounded-[4px] bg-[var(--surface-1)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-secondary)]"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <Button type="button" variant="secondary" size="sm" disabled title="Coming soon">
                  <Play className="h-3 w-3" />
                  Preview
                </Button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {SFX.map((s) => (
            <div
              key={s.id}
              className="rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[14px] font-semibold">{s.name}</p>
                  <p className="mt-1 text-[12px] text-[var(--text-secondary)]">{s.category}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {s.tags.map((tag) => (
                      <span
                        key={tag}
                        className="rounded-[4px] bg-[var(--surface-1)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-secondary)]"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <Button type="button" variant="secondary" size="sm" disabled title="Coming soon">
                  <Play className="h-3 w-3" />
                  Preview
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
