import { Play, UserRound } from 'lucide-react'
import { useState } from 'react'

import { AddAssetMenu } from '@/components/AddAssetMenu'
import { ListingEmptyState, ListingShell, PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

/** Demo library cards — filled for casting / mix UI. */
const CHARACTERS = [
  {
    id: 'c1',
    name: 'Inspector Mehra',
    role: 'Protagonist',
    voice: 'NARRATOR Calm → mature command',
    age: '40s',
    vibe: 'Measured, clipped, late-night case files',
  },
  {
    id: 'c2',
    name: 'Riya Sharma',
    role: 'Lead',
    voice: 'RIYA Soft',
    age: '20s',
    vibe: 'Nervous warmth, Hinglish under stress',
  },
  {
    id: 'c3',
    name: 'Arjun Malhotra',
    role: 'Ally',
    voice: 'ARJUN Steady',
    age: '30s',
    vibe: 'Protector energy, low and steady',
  },
  {
    id: 'c4',
    name: 'The Caller',
    role: 'Antagonist',
    voice: 'THE VOICE',
    age: 'Unknown',
    vibe: 'Distorted whisper, never fully human',
  },
  {
    id: 'c5',
    name: 'ACP Dayal',
    role: 'Authority',
    voice: 'DAYAL Gravitas',
    age: '50s',
    vibe: 'Crime-procedural bark, short orders',
  },
  {
    id: 'c6',
    name: 'Meera Kapoor',
    role: 'Witness',
    voice: 'MEERA Soft',
    age: '30s',
    vibe: 'Hesitant confession, kitchen-radio quiet',
  },
  {
    id: 'c7',
    name: 'Kabir / Chetak',
    role: 'Side / animal',
    voice: 'FX Breath',
    age: '—',
    vibe: 'Breath, whinny, non-verbal presence',
  },
  {
    id: 'c8',
    name: 'Series Narrator',
    role: 'Guide',
    voice: 'HOST Warm / NARRATOR Dark',
    age: '—',
    vibe: 'Pocket FM bridge lines, cliff hooks',
  },
]

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
    id: 'n2',
    name: 'NARRATOR Dark',
    lang: 'Hindi',
    style: 'Noir serial bed',
    tags: ['narrator', 'hindi'],
    elevenLabsVoiceId: 'nPczCjzI2devNBz1zQrb',
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
  {
    id: 'd1',
    name: 'DAYAL Gravitas',
    lang: 'Hindi',
    style: 'Senior officer',
    tags: ['character', 'authority'],
    elevenLabsVoiceId: 'pqHfZKP75CvOlQylNhV4',
  },
  {
    id: 'm1',
    name: 'MEERA Soft',
    lang: 'Hindi',
    style: 'Witness / confidante',
    tags: ['character'],
    elevenLabsVoiceId: 'XrExE9yKIg1WjnnlVkGX',
  },
  {
    id: 'k1',
    name: 'KABIR Sharp',
    lang: 'English',
    style: 'Antagonist edge',
    tags: ['character', 'villain'],
    elevenLabsVoiceId: 'onwK4e9ZLuTAKqWW03F9',
  },
  {
    id: 's1v',
    name: 'SANA Bright',
    lang: 'Hinglish',
    style: 'Campus / young lead',
    tags: ['character', 'youth'],
    elevenLabsVoiceId: 'ThT5KcBeYPX3keUQqHPh',
  },
  {
    id: 'f1',
    name: 'FX Breath',
    lang: 'Neutral',
    style: 'Non-verbal / creature',
    tags: ['fx-voice'],
    elevenLabsVoiceId: 'VR6AewLTigWG4xSOukaG',
  },
  {
    id: 'p1',
    name: 'PRIYA Warm',
    lang: 'Hindi',
    style: 'Loyalty listener energy',
    tags: ['character'],
    elevenLabsVoiceId: 'EXAVITQu4vr4xnSDxMaL',
  },
]

const SFX = [
  { id: 's1', name: 'Door creak', category: 'Foley', tags: ['interior'] },
  { id: 's2', name: 'Distant thunder', category: 'Ambience', tags: ['weather'] },
  { id: 's3', name: 'Footsteps wood', category: 'Foley', tags: ['movement'] },
  { id: 's4', name: 'Heartbeat low', category: 'Tension', tags: ['score-bed'] },
  { id: 's5', name: 'City night bed', category: 'Ambience', tags: ['exterior'] },
  { id: 's6', name: 'Radio static sting', category: 'Transition', tags: ['sting'] },
  { id: 's7', name: 'Phone vibrate table', category: 'Foley', tags: ['prop'] },
  { id: 's8', name: 'Rain on tin roof', category: 'Ambience', tags: ['weather'] },
  { id: 's9', name: 'Gunshot distant', category: 'Impact', tags: ['action'] },
  { id: 's10', name: 'Horse whinny', category: 'Creature', tags: ['animal'] },
  { id: 's11', name: 'Crowd murmur bazaar', category: 'Ambience', tags: ['exterior'] },
  { id: 's12', name: 'Police siren pass', category: 'Exterior', tags: ['city'] },
  { id: 's13', name: 'Keyboard typing', category: 'Foley', tags: ['office'] },
  { id: 's14', name: 'Glass shatter', category: 'Impact', tags: ['action'] },
  { id: 's15', name: 'Temple bell soft', category: 'Ambience', tags: ['cultural'] },
  { id: 's16', name: 'Suspense riser', category: 'Transition', tags: ['score-bed'] },
  { id: 's17', name: 'Car door slam', category: 'Foley', tags: ['vehicle'] },
  { id: 's18', name: 'Whisper room tone', category: 'Tension', tags: ['interior'] },
]

type Tab = 'characters' | 'voices' | 'sfx'

type LocalAudio = {
  id: string
  name: string
  kind: Tab
  sizeLabel: string
}

function formatBytes(n: number) {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

export function LibraryPage() {
  const [tab, setTab] = useState<Tab>('characters')
  const [uploads, setUploads] = useState<LocalAudio[]>([])

  const onAudioFiles = async (files: File[]) => {
    const kind: Tab = tab === 'characters' ? 'voices' : tab
    const next = files.map((file) => ({
      id: `${Date.now()}-${file.name}`,
      name: file.name,
      kind,
      sizeLabel: formatBytes(file.size),
    }))
    setUploads((prev) => [...next, ...prev])
  }

  return (
    <ListingShell maxWidth="4xl">
      <PageHeader
        title="Library"
        description="Characters, voices, and sound effects for casting and mix. Preview is demo-only for now."
        actions={
          <AddAssetMenu
            actions={[
              {
                kind: 'audio',
                label: 'Add audio',
                accept: 'audio/*,.mp3,.wav,.m4a,.ogg',
                multiple: true,
                hint:
                  tab === 'sfx'
                    ? 'SFX / ambience clip'
                    : 'Voice sample for this library',
                onFiles: onAudioFiles,
              },
            ]}
          />
        }
      >
        <div className="mt-5 flex gap-1 rounded-[8px] bg-[var(--surface-1)] p-1 w-fit">
          {(
            [
              { id: 'characters', label: 'Characters' },
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
      </PageHeader>

      {uploads.filter((u) => u.kind === tab || (tab === 'characters' && u.kind === 'voices'))
        .length > 0 ? (
        <div className="mb-4 space-y-2">
          <p className="text-[12px] font-medium text-[var(--text-secondary)]">Your uploads</p>
          {uploads
            .filter((u) => u.kind === tab || (tab === 'characters' && u.kind === 'voices'))
            .map((u) => (
              <div
                key={u.id}
                className="flex items-center justify-between gap-3 rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] px-4 py-3"
              >
                <div className="min-w-0">
                  <p className="truncate text-[13px] font-medium">{u.name}</p>
                  <p className="mt-0.5 text-[11px] text-[var(--text-secondary)]">{u.sizeLabel}</p>
                </div>
                <span className="shrink-0 text-[11px] text-[var(--text-secondary)]">Staged</span>
              </div>
            ))}
        </div>
      ) : null}

      {tab === 'characters' ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {CHARACTERS.map((c) => (
            <div
              key={c.id}
              className="rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-4"
            >
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[8px] bg-[var(--surface-1)] text-[var(--brand)]">
                  <UserRound className="h-5 w-5 stroke-[1.75]" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[14px] font-semibold">{c.name}</p>
                  <p className="mt-0.5 text-[12px] text-[var(--text-secondary)]">
                    {c.role} · {c.age}
                  </p>
                  <p className="mt-2 text-[12px] leading-5 text-[var(--text-secondary)]">{c.vibe}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    <span className="rounded-[4px] bg-[var(--surface-1)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-secondary)]">
                      {c.voice}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {tab === 'voices' ? (
        VOICES.length === 0 ? (
          <ListingEmptyState
            title="No voices yet"
            description="Add an audio sample with + Add."
          />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
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
        )
      ) : null}

      {tab === 'sfx' ? (
        SFX.length === 0 ? (
          <ListingEmptyState title="No sound effects yet" description="Add an audio clip with + Add." />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
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
        )
      ) : null}
    </ListingShell>
  )
}

/** @deprecated Use LibraryPage — kept for any lingering imports */
export const VoiceLibraryPage = LibraryPage
