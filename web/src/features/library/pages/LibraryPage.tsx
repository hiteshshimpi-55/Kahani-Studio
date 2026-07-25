import { Play } from 'lucide-react'
import { useState } from 'react'

import { AddAssetMenu } from '@/components/AddAssetMenu'
import { ListingEmptyState, ListingShell, PageHeader } from '@/components/layout/PageHeader'
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
  const [tab, setTab] = useState<Tab>('voices')
  const [uploads, setUploads] = useState<LocalAudio[]>([])

  const onAudioFiles = async (files: File[]) => {
    const next = files.map((file) => ({
      id: `${Date.now()}-${file.name}`,
      name: file.name,
      kind: tab,
      sizeLabel: formatBytes(file.size),
    }))
    setUploads((prev) => [...next, ...prev])
  }

  return (
    <ListingShell maxWidth="4xl">
      <PageHeader
        title="Library"
        description="Global voices and sound effects for casting and mix. Preview is demo-only for now."
        actions={
          <AddAssetMenu
            actions={[
              {
                kind: 'audio',
                label: 'Add audio',
                accept: 'audio/*,.mp3,.wav,.m4a,.ogg',
                multiple: true,
                hint: tab === 'voices' ? 'Voice sample for this library' : 'SFX / ambience clip',
                onFiles: onAudioFiles,
              },
            ]}
          />
        }
      >
        <div className="mt-5 flex gap-1 rounded-[8px] bg-[var(--surface-1)] p-1 w-fit">
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
      </PageHeader>

      {uploads.filter((u) => u.kind === tab).length > 0 ? (
        <div className="mb-4 space-y-2">
          <p className="text-[12px] font-medium text-[var(--text-secondary)]">Your uploads</p>
          {uploads
            .filter((u) => u.kind === tab)
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
      ) : SFX.length === 0 ? (
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
      )}
    </ListingShell>
  )
}

/** @deprecated Use LibraryPage — kept for any lingering imports */
export const VoiceLibraryPage = LibraryPage
