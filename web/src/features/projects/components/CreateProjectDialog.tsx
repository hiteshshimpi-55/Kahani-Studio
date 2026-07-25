import { useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Dialog } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'

interface Props {
  open: boolean
  onClose: () => void
  onCreate: (input: { name: string; description?: string }) => Promise<unknown>
}

export function CreateProjectDialog({ open, onClose, onCreate }: Props) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) {
      setError('Name is required')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      await onCreate({
        name: name.trim(),
        description: description.trim() || undefined,
      })
      setName('')
      setDescription('')
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create project')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="New project"
      description="Give your story a name. You can attach context and generate from the project page."
    >
      <form className="space-y-4" onSubmit={(e) => void handleSubmit(e)}>
        <div className="space-y-1.5">
          <label htmlFor="project-name" className="text-[13px] font-medium text-[var(--text-primary)]">
            Name
          </label>
          <Input
            id="project-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Midnight House"
            autoFocus
            required
          />
        </div>
        <div className="space-y-1.5">
          <label htmlFor="project-desc" className="text-[13px] font-medium text-[var(--text-primary)]">
            Description{' '}
            <span className="font-normal text-[var(--text-secondary)]">(optional)</span>
          </label>
          <Textarea
            id="project-desc"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Short pitch or series notes"
            rows={3}
            className="text-[13px]"
          />
        </div>
        {error ? <p className="text-[13px] text-destructive">{error}</p> : null}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? 'Creating…' : 'Create project'}
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
