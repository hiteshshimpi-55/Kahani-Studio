import { useCallback, useEffect, useRef, useState } from 'react'

import * as api from '../api/projects-api'
import type { ProjectAttachment } from '../types'

export function useAttachments(projectId: string | undefined) {
  const [attachments, setAttachments] = useState<ProjectAttachment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const pollRef = useRef<number | null>(null)

  const refresh = useCallback(async () => {
    if (!projectId) return
    try {
      const rows = await api.listAttachments(projectId)
      setAttachments(rows)
      setError(null)
      return rows
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load attachments')
      return []
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    setLoading(true)
    void refresh()
  }, [refresh])

  useEffect(() => {
    const pending = attachments.some((a) => a.index_status === 'pending')
    if (!pending || !projectId) {
      if (pollRef.current) {
        window.clearInterval(pollRef.current)
        pollRef.current = null
      }
      return
    }
    pollRef.current = window.setInterval(() => {
      void refresh()
    }, 2000)
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current)
    }
  }, [attachments, projectId, refresh])

  const upload = useCallback(
    async (files: FileList | File[]) => {
      if (!projectId) return
      setUploading(true)
      setError(null)
      try {
        const list = Array.from(files)
        for (const file of list) {
          const row = await api.uploadAttachment(projectId, file)
          setAttachments((prev) => [row, ...prev])
        }
        await refresh()
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Upload failed')
      } finally {
        setUploading(false)
      }
    },
    [projectId, refresh],
  )

  const remove = useCallback(
    async (attachmentId: string) => {
      if (!projectId) return
      try {
        await api.deleteAttachment(projectId, attachmentId)
        setAttachments((prev) => prev.filter((a) => a.id !== attachmentId))
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Delete failed')
      }
    },
    [projectId],
  )

  return { attachments, loading, error, uploading, refresh, upload, remove }
}
