import { useState } from 'react'
import { Pencil, Trash2, Check, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

import type { ProjectCharacter } from '../types'

interface Props {
  characters: ProjectCharacter[]
  loading: boolean
  error: string | null
  onUpdate: (
    id: string,
    body: Partial<Pick<ProjectCharacter, 'name' | 'role' | 'voice' | 'speech_patterns' | 'arc'>>,
  ) => Promise<void>
  onDelete: (id: string) => Promise<void>
}

export function CastPanel({ characters, loading, error, onUpdate, onDelete }: Props) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [draft, setDraft] = useState<Partial<ProjectCharacter>>({})
  const [busy, setBusy] = useState(false)

  const startEdit = (ch: ProjectCharacter) => {
    setEditingId(ch.id)
    setDraft({
      name: ch.name,
      role: ch.role ?? '',
      voice: ch.voice ?? '',
      speech_patterns: ch.speech_patterns ?? '',
      arc: ch.arc ?? '',
    })
  }

  const save = async (id: string) => {
    setBusy(true)
    try {
      await onUpdate(id, {
        name: draft.name || undefined,
        role: draft.role ?? '',
        voice: draft.voice ?? '',
        speech_patterns: draft.speech_patterns ?? '',
        arc: draft.arc ?? '',
      })
      setEditingId(null)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-5">
      <div className="mb-4">
        <h2 className="text-[14px] font-semibold text-[var(--text-primary)]">Cast</h2>
        <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
          Series characters locked into every new episode. Grown automatically from each script.
        </p>
      </div>

      {error ? (
        <p className="mb-3 text-[13px] text-[var(--danger)]">{error}</p>
      ) : null}

      {loading && characters.length === 0 ? (
        <p className="text-[13px] text-[var(--text-secondary)]">Loading cast…</p>
      ) : null}

      {!loading && characters.length === 0 ? (
        <p className="text-[13px] text-[var(--text-secondary)]">
          Generate an episode to grow the cast.
        </p>
      ) : null}

      <ul className="space-y-3">
        {characters.map((ch) => {
          const editing = editingId === ch.id
          return (
            <li
              key={ch.id}
              className="rounded-[8px] border border-[var(--folio-border)] bg-[var(--surface-0)] px-3 py-3"
            >
              {editing ? (
                <div className="space-y-2">
                  <Input
                    value={draft.name ?? ''}
                    onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))}
                    placeholder="Name"
                  />
                  <Input
                    value={draft.role ?? ''}
                    onChange={(e) => setDraft((d) => ({ ...d, role: e.target.value }))}
                    placeholder="Role"
                  />
                  <Input
                    value={draft.voice ?? ''}
                    onChange={(e) => setDraft((d) => ({ ...d, voice: e.target.value }))}
                    placeholder="Voice"
                  />
                  <Input
                    value={draft.speech_patterns ?? ''}
                    onChange={(e) =>
                      setDraft((d) => ({ ...d, speech_patterns: e.target.value }))
                    }
                    placeholder="Speech patterns"
                  />
                  <Input
                    value={draft.arc ?? ''}
                    onChange={(e) => setDraft((d) => ({ ...d, arc: e.target.value }))}
                    placeholder="Arc"
                  />
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      size="sm"
                      disabled={busy}
                      onClick={() => void save(ch.id)}
                    >
                      <Check className="size-3.5" />
                      Save
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => setEditingId(null)}
                    >
                      <X className="size-3.5" />
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-[14px] font-medium text-[var(--text-primary)]">
                      {ch.name}
                      {ch.role ? (
                        <span className="ml-2 text-[12px] font-normal text-[var(--text-secondary)]">
                          {ch.role}
                        </span>
                      ) : null}
                    </p>
                    {ch.voice ? (
                      <p className="mt-1 text-[12px] text-[var(--text-secondary)]">{ch.voice}</p>
                    ) : null}
                    {ch.speech_patterns ? (
                      <p className="mt-0.5 text-[12px] text-[var(--text-secondary)]">
                        {ch.speech_patterns}
                      </p>
                    ) : null}
                    {ch.arc ? (
                      <p className="mt-0.5 text-[12px] italic text-[var(--text-secondary)]">
                        {ch.arc}
                      </p>
                    ) : null}
                  </div>
                  <div className="flex shrink-0 gap-1">
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      className="px-2"
                      aria-label="Edit character"
                      onClick={() => startEdit(ch)}
                    >
                      <Pencil className="size-3.5" />
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      className="px-2"
                      aria-label="Delete character"
                      onClick={() => void onDelete(ch.id)}
                    >
                      <Trash2 className="size-3.5" />
                    </Button>
                  </div>
                </div>
              )}
            </li>
          )
        })}
      </ul>
    </section>
  )
}
