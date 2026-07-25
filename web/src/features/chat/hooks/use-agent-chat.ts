import { useCallback, useEffect, useRef, useState } from 'react'

import * as projectsApi from '@/features/projects/api/projects-api'
import type { ProjectAttachment, ProjectRun } from '@/features/projects/types'

import { GRAPH_TOOL_STEPS, type AgentToolStep, type ChatMessage } from '../types'

function uid() {
  return crypto.randomUUID()
}

function freshTools(): AgentToolStep[] {
  return GRAPH_TOOL_STEPS.map((s) => ({ ...s, status: 'pending' as const }))
}

function advanceTools(tools: AgentToolStep[], upToIndex: number): AgentToolStep[] {
  return tools.map((t, i) => {
    if (i < upToIndex) return { ...t, status: 'done' }
    if (i === upToIndex) return { ...t, status: 'running' }
    return { ...t, status: 'pending' }
  })
}

function completeTools(tools: AgentToolStep[]): AgentToolStep[] {
  return tools.map((t) => ({ ...t, status: 'done' }))
}

function runToMessages(run: ProjectRun): ChatMessage[] {
  const createdAt = new Date(run.created_at).getTime()
  const userMsg: ChatMessage = {
    id: `user-${run.id}`,
    role: 'user',
    content: run.prompt,
    createdAt,
  }

  if (run.status === 'queued' || run.status === 'running') {
    return [
      userMsg,
      {
        id: `assistant-${run.id}`,
        role: 'assistant',
        content: '',
        createdAt: createdAt + 1,
        tools: advanceTools(freshTools(), 1),
        runId: run.id,
        status: 'streaming',
      },
    ]
  }

  if (run.status === 'failed') {
    return [
      userMsg,
      {
        id: `assistant-${run.id}`,
        role: 'assistant',
        content: run.error || 'Generation failed.',
        createdAt: createdAt + 1,
        runId: run.id,
        status: 'error',
        tools: freshTools().map((t, i) =>
          i < 2 ? { ...t, status: 'done' } : { ...t, status: i === 2 ? 'error' : 'pending' },
        ),
      },
    ]
  }

  const preview = run.screenplay_md || run.screenplay_preview || ''
  return [
    userMsg,
    {
      id: `assistant-${run.id}`,
      role: 'assistant',
      content: run.is_draft
        ? 'Script Writer finished. This output is saved as a draft — edit it here or open Drafts.'
        : 'Script Writer finished. Review the output below, then add it as a draft when you’re ready.',
      createdAt: createdAt + 1,
      tools: completeTools(freshTools()),
      runId: run.id,
      scriptId: run.draft_script_id ?? undefined,
      scriptPreview: preview || undefined,
      isDraft: Boolean(run.is_draft),
      status: 'complete',
    },
  ]
}

export function useAgentChat(projectId: string | undefined) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [hydrating, setHydrating] = useState(true)
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollRef = useRef<number | null>(null)
  const stepTimerRef = useRef<number | null>(null)

  const clearTimers = useCallback(() => {
    if (pollRef.current) {
      window.clearInterval(pollRef.current)
      pollRef.current = null
    }
    if (stepTimerRef.current) {
      window.clearInterval(stepTimerRef.current)
      stepTimerRef.current = null
    }
  }, [])

  const updateAssistant = useCallback((assistantId: string, patch: Partial<ChatMessage>) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === assistantId ? { ...m, ...patch } : m)),
    )
  }, [])

  const pollUntilDone = useCallback(
    (assistantId: string, runId: string) => {
      if (!projectId) return Promise.resolve()
      return new Promise<void>((resolve, reject) => {
        pollRef.current = window.setInterval(async () => {
          try {
            const next = await projectsApi.getRun(projectId, runId)
            if (next.status === 'succeeded') {
              clearTimers()
              const preview = next.screenplay_md || next.screenplay_preview || ''
              updateAssistant(assistantId, {
                tools: completeTools(freshTools()),
                content: next.is_draft
                  ? 'Script Writer finished. This output is saved as a draft — edit it here or open Drafts.'
                  : 'Script Writer finished. Review the output below, then add it as a draft when you’re ready.',
                scriptPreview: preview || 'Script generated successfully.',
                scriptId: next.draft_script_id ?? undefined,
                isDraft: Boolean(next.is_draft),
                status: 'complete',
              })
              setStreaming(false)
              resolve()
            } else if (next.status === 'failed') {
              clearTimers()
              updateAssistant(assistantId, {
                tools: freshTools().map((t, i) =>
                  i < 2 ? { ...t, status: 'done' } : { ...t, status: i === 2 ? 'error' : 'pending' },
                ),
                content: next.error || 'Generation failed.',
                status: 'error',
              })
              setStreaming(false)
              setError(next.error)
              reject(new Error(next.error || 'failed'))
            }
          } catch {
            /* keep polling */
          }
        }, 2000)
      })
    },
    [projectId, clearTimers, updateAssistant],
  )

  useEffect(() => {
    if (!projectId) {
      setMessages([])
      setHydrating(false)
      return
    }

    let cancelled = false
    clearTimers()
    setHydrating(true)
    setStreaming(false)
    setError(null)

    void (async () => {
      try {
        const runs = await projectsApi.listRuns(projectId)
        if (cancelled) return
        setMessages(runs.flatMap(runToMessages))

        const inFlight = [...runs].reverse().find(
          (r) => r.status === 'queued' || r.status === 'running',
        )
        if (inFlight) {
          setStreaming(true)
          const assistantId = `assistant-${inFlight.id}`
          let stepIndex = 1
          stepTimerRef.current = window.setInterval(() => {
            stepIndex = Math.min(stepIndex + 1, GRAPH_TOOL_STEPS.length - 2)
            updateAssistant(assistantId, {
              tools: advanceTools(freshTools(), stepIndex),
            })
          }, 2200)
          try {
            await pollUntilDone(assistantId, inFlight.id)
          } catch {
            /* surfaced on message */
          }
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load chat')
        }
      } finally {
        if (!cancelled) setHydrating(false)
      }
    })()

    return () => {
      cancelled = true
      clearTimers()
    }
    // Intentionally only re-hydrate when project changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  const send = useCallback(
    async (text: string) => {
      if (!projectId || !text.trim() || streaming) return
      setError(null)
      setStreaming(true)

      const userMsg: ChatMessage = {
        id: uid(),
        role: 'user',
        content: text.trim(),
        createdAt: Date.now(),
      }
      const assistantId = uid()
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: 'assistant',
        content: '',
        createdAt: Date.now(),
        tools: freshTools(),
        status: 'streaming',
      }
      setMessages((prev) => [...prev, userMsg, assistantMsg])

      let stepIndex = 0
      updateAssistant(assistantId, { tools: advanceTools(freshTools(), 0) })
      stepTimerRef.current = window.setInterval(() => {
        stepIndex = Math.min(stepIndex + 1, GRAPH_TOOL_STEPS.length - 2)
        updateAssistant(assistantId, {
          tools: advanceTools(freshTools(), stepIndex),
        })
      }, 2200)

      try {
        const run = await projectsApi.startRun(projectId, { prompt: text.trim() })
        updateAssistant(assistantId, { runId: run.id })
        await pollUntilDone(assistantId, run.id)
      } catch (e) {
        clearTimers()
        const msg = e instanceof Error ? e.message : 'Failed to start run'
        setError(msg)
        updateAssistant(assistantId, {
          content: msg,
          status: 'error',
          tools: freshTools().map((t, i) => (i === 0 ? { ...t, status: 'error' } : t)),
        })
        setStreaming(false)
      }
    },
    [projectId, streaming, clearTimers, updateAssistant, pollUntilDone],
  )

  const saveDraft = useCallback(
    async (runId: string, assistantId: string, screenplay_md?: string) => {
      if (!projectId) return
      try {
        const script = await projectsApi.saveRunAsDraft(projectId, runId, screenplay_md)
        updateAssistant(assistantId, {
          scriptId: script.id,
          isDraft: true,
          scriptPreview: script.screenplay_md,
          content:
            'Draft saved. You can keep editing it here, or open it from Drafts / Editor.',
        })
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to save draft')
      }
    },
    [projectId, updateAssistant],
  )

  const updateDraft = useCallback(
    async (scriptId: string, assistantId: string, screenplay_md: string) => {
      if (!projectId) return
      try {
        const script = await projectsApi.updateScript(projectId, scriptId, screenplay_md)
        updateAssistant(assistantId, {
          scriptPreview: script.screenplay_md,
          isDraft: true,
        })
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to update draft')
        throw e
      }
    },
    [projectId, updateAssistant],
  )

  const attach = useCallback(
    async (file: File): Promise<ProjectAttachment | null> => {
      if (!projectId) return null
      try {
        return await projectsApi.uploadAttachment(projectId, file)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Upload failed')
        return null
      }
    },
    [projectId],
  )

  return {
    messages,
    hydrating,
    streaming,
    error,
    send,
    attach,
    saveDraft,
    updateDraft,
  }
}
