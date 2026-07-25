import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { AddAssetMenu } from '@/components/AddAssetMenu'
import { ListingEmptyState, ListingShell, PageHeader } from '@/components/layout/PageHeader'
import { KissaLoader } from '@/components/ui/kissa-loader'
import { useProject } from '@/features/projects/hooks/use-project'
import { NotFoundView } from '@/features/system/pages/NotFoundPage'

type LocalVisual = {
  id: string
  name: string
  sizeLabel: string
}

function formatBytes(n: number) {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

export function ProjectVisualsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { project, loading, error } = useProject(projectId)
  const [uploads, setUploads] = useState<LocalVisual[]>([])

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <KissaLoader label="Loading visuals…" />
      </div>
    )
  }
  if (error || !project) {
    return (
      <NotFoundView
        kind="project"
        detail={error && error !== 'Not found' && error !== 'Project not found' ? error : null}
      />
    )
  }

  return (
    <ListingShell maxWidth="3xl">
      <PageHeader
        title="Visuals"
        description="Companion frames for the editor. Generated visuals attach after a draft; you can also stage reference images."
        breadcrumb={
          <Link to={`/projects/${project.id}/chat`} className="hover:text-[var(--brand)]">
            {project.name}
          </Link>
        }
        actions={
          <AddAssetMenu
            actions={[
              {
                kind: 'visual',
                label: 'Add visual',
                accept: 'image/*,.png,.jpg,.jpeg,.webp',
                multiple: true,
                hint: 'Reference still (staged locally for now)',
                onFiles: async (files) => {
                  setUploads((prev) => [
                    ...files.map((f) => ({
                      id: `${Date.now()}-${f.name}`,
                      name: f.name,
                      sizeLabel: formatBytes(f.size),
                    })),
                    ...prev,
                  ])
                },
              },
            ]}
          />
        }
      />

      {uploads.length > 0 ? (
        <div className="mb-4 space-y-2">
          {uploads.map((u) => (
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

      {uploads.length === 0 ? (
        <ListingEmptyState
          title="No visuals yet"
          description="Generate a script draft first, or stage a reference image with + Add."
          action={
            <Link
              to={`/projects/${project.id}/chat`}
              className="text-[13px] font-medium text-[var(--brand)] hover:underline"
            >
              Open chat
            </Link>
          }
        />
      ) : null}
    </ListingShell>
  )
}
