import { useCallback, useEffect, useRef, useState } from 'react'

import * as projectsApi from '@/features/projects/api/projects-api'
import type { ChatSession, ProjectAttachment } from '@/features/projects/types'

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

function historyToMessages(
  items: Awaited<ReturnType<typeof projectsApi.listChatMessages>>,
): ChatMessage[] {
  return items.map((item) => {
    const createdAt = new Date(item.created_at).getTime()
    if (item.role === 'user') {
      return {
        id: item.id,
        role: 'user' as const,
        content: item.content,
        createdAt,
        kind: 'user' as const,
        status: 'complete' as const,
      }
    }

    const runStatus = item.run_status
    if (item.kind === 'generating' || runStatus === 'queued' || runStatus === 'running') {
      if (runStatus === 'succeeded') {
        return {
          id: item.id,
          role: 'assistant' as const,
          content:
            item.content ||
            'Script is ready. Review it below — save as a draft when you want to keep it.',
          createdAt,
          kind: 'script' as const,
          runId: item.run_id ?? undefined,
          scriptPreview: item.script_preview ?? undefined,
          scriptId: item.draft_script_id ?? undefined,
          isDraft: Boolean(item.is_draft),
          tools: completeTools(freshTools()),
          status: 'complete' as const,
        }
      }
      if (runStatus === 'failed') {
        return {
          id: item.id,
          role: 'assistant' as const,
          content: item.content || 'Generation failed.',
          createdAt,
          kind: 'generating' as const,
          runId: item.run_id ?? undefined,
          status: 'error' as const,
          tools: freshTools().map((t, i) =>
            i < 1 ? { ...t, status: 'done' } : { ...t, status: i === 1 ? 'error' : 'pending' },
          ),
        }
      }
      if (runStatus === 'cancelled') {
        return {
          id: item.id,
          role: 'assistant' as const,
          content: 'Stopped. Tell me what to change, or ask me to continue.',
          createdAt,
          kind: 'stopped' as const,
          runId: item.run_id ?? undefined,
          status: 'stopped' as const,
        }
      }
      return {
        id: item.id,
        role: 'assistant' as const,
        content: item.content,
        createdAt,
        kind: 'generating' as const,
        runId: item.run_id ?? undefined,
        tools: advanceTools(freshTools(), 1),
        status: 'streaming' as const,
      }
    }

    return {
      id: item.id,
      role: 'assistant' as const,
      content: item.content,
      createdAt,
      kind: (item.kind as ChatMessage['kind']) || 'reply',
      questions: item.questions,
      runId: item.run_id ?? undefined,
      scriptPreview: item.script_preview ?? undefined,
      scriptId: item.draft_script_id ?? undefined,
      isDraft: Boolean(item.is_draft),
      status: 'complete' as const,
      tools:
        item.script_preview || item.kind === 'script'
          ? completeTools(freshTools())
          : undefined,
    }
  })
}

export function useAgentChat(projectId: string | undefined) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [hydrating, setHydrating] = useState(true)
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollRef = useRef<number | null>(null)
  const stepTimerRef = useRef<number | null>(null)
  const activeSessionRef = useRef<string | null>(null)
  const activeRunRef = useRef<string | null>(null)
  const activeAssistantRef = useRef<string | null>(null)

  useEffect(() => {
    activeSessionRef.current = activeSessionId
  }, [activeSessionId])

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

  const refreshSessions = useCallback(async () => {
    if (!projectId) return []
    const next = await projectsApi.listSessions(projectId)
    setSessions(next)
    return next
  }, [projectId])

  const pollUntilDone = useCallback(
    (assistantId: string, runId: string) => {
      if (!projectId) return Promise.resolve()
      activeRunRef.current = runId
      activeAssistantRef.current = assistantId
      return new Promise<void>((resolve) => {
        pollRef.current = window.setInterval(async () => {
          try {
            const next = await projectsApi.getRun(projectId, runId)
            if (next.status === 'succeeded') {
              clearTimers()
              const preview = next.screenplay_md || next.screenplay_preview || ''
              updateAssistant(assistantId, {
                tools: completeTools(freshTools()),
                content:
                  'Script Writer finished. Review the screenplay below — save it as a draft when you’re happy with it.',
                scriptPreview: preview || 'Script generated successfully.',
                scriptId: next.draft_script_id ?? undefined,
                isDraft: Boolean(next.is_draft),
                kind: 'script',
                status: 'complete',
              })
              activeRunRef.current = null
              setStreaming(false)
              void refreshSessions()
              resolve()
            } else if (next.status === 'failed') {
              clearTimers()
              updateAssistant(assistantId, {
                tools: freshTools().map((t, i) =>
                  i < 1 ? { ...t, status: 'done' } : { ...t, status: i === 1 ? 'error' : 'pending' },
                ),
                content: next.error || 'Generation failed.',
                status: 'error',
              })
              activeRunRef.current = null
              setStreaming(false)
              setError(next.error)
              resolve()
            } else if (next.status === 'cancelled') {
              clearTimers()
              updateAssistant(assistantId, {
                content: 'Stopped. Tell me what to change, or ask me to continue.',
                tools: undefined,
                kind: 'stopped',
                status: 'stopped',
              })
              activeRunRef.current = null
              setStreaming(false)
              resolve()
            }
          } catch {
            /* keep polling */
          }
        }, 2000)
      })
    },
    [projectId, clearTimers, updateAssistant, refreshSessions],
  )

  const loadSession = useCallback(
    async (sessionId: string) => {
      if (!projectId) return
      clearTimers()
      setHydrating(true)
      setStreaming(false)
      setError(null)
      setActiveSessionId(sessionId)
      activeRunRef.current = null
      try {
        const history = await projectsApi.listChatMessages(projectId, sessionId)
        const mapped = historyToMessages(history)
        setMessages(mapped)

        const inFlight = [...mapped].reverse().find((m) => m.status === 'streaming' && m.runId)
        if (inFlight?.runId) {
          setStreaming(true)
          let stepIndex = 1
          stepTimerRef.current = window.setInterval(() => {
            stepIndex = Math.min(stepIndex + 1, GRAPH_TOOL_STEPS.length - 2)
            updateAssistant(inFlight.id, {
              tools: advanceTools(freshTools(), stepIndex),
            })
          }, 2200)
          await pollUntilDone(inFlight.id, inFlight.runId)
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load chat')
      } finally {
        setHydrating(false)
      }
    },
    [projectId, clearTimers, updateAssistant, pollUntilDone],
  )

  useEffect(() => {
    if (!projectId) {
      setMessages([])
      setSessions([])
      setActiveSessionId(null)
      setHydrating(false)
      return
    }

    let cancelled = false
    clearTimers()
    setHydrating(true)

    void (async () => {
      try {
        const list = await projectsApi.listSessions(projectId)
        if (cancelled) return
        setSessions(list)
        const active = list[0]?.id
        if (active) await loadSession(active)
        else {
          setMessages([])
          setHydrating(false)
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load chat')
          setHydrating(false)
        }
      }
    })()

    return () => {
      cancelled = true
      clearTimers()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  const send = useCallback(
    async (text: string) => {
      if (!projectId || !text.trim() || streaming) return
      setError(null)

      const userMsg: ChatMessage = {
        id: uid(),
        role: 'user',
        content: text.trim(),
        createdAt: Date.now(),
        kind: 'user',
        status: 'complete',
      }
      const thinkingId = uid()
      setMessages((prev) => [
        ...prev,
        userMsg,
        {
          id: thinkingId,
          role: 'assistant',
          content: '',
          createdAt: Date.now(),
          tools: advanceTools(freshTools(), 0),
          status: 'streaming',
          kind: 'generating',
        },
      ])
      setStreaming(true)

      try {
        const sessionId = activeSessionRef.current ?? undefined
        const result = await projectsApi.postChatMessage(projectId, text.trim(), sessionId)
        if (result.session_id && result.session_id !== activeSessionRef.current) {
          setActiveSessionId(result.session_id)
        }

        if (result.kind === 'generating' && result.run_id) {
          updateAssistant(thinkingId, {
            id: result.id,
            content: result.content,
            runId: result.run_id,
            kind: 'generating',
            tools: advanceTools(freshTools(), 1),
            status: 'streaming',
          })
          // Remap id for subsequent updates
          setMessages((prev) =>
            prev.map((m) => (m.id === thinkingId ? { ...m, id: result.id } : m)),
          )
          activeAssistantRef.current = result.id
          let stepIndex = 1
          stepTimerRef.current = window.setInterval(() => {
            stepIndex = Math.min(stepIndex + 1, GRAPH_TOOL_STEPS.length - 2)
            updateAssistant(result.id, {
              tools: advanceTools(freshTools(), stepIndex),
            })
          }, 2200)
          await pollUntilDone(result.id, result.run_id)
          return
        }

        clearTimers()
        updateAssistant(thinkingId, {
          id: result.id,
          content: result.content,
          kind: result.kind as ChatMessage['kind'],
          questions: result.questions,
          tools: undefined,
          status: 'complete',
        })
        setMessages((prev) =>
          prev.map((m) =>
            m.id === thinkingId
              ? {
                  ...m,
                  id: result.id,
                  content: result.content,
                  kind: result.kind as ChatMessage['kind'],
                  questions: result.questions,
                  tools: undefined,
                  status: 'complete',
                }
              : m,
          ),
        )
        setStreaming(false)
        void refreshSessions()
      } catch (e) {
        clearTimers()
        const msg = e instanceof Error ? e.message : 'Failed to send message'
        setError(msg)
        updateAssistant(thinkingId, {
          content: msg,
          status: 'error',
          tools: freshTools().map((t, i) => (i === 0 ? { ...t, status: 'error' } : t)),
        })
        setStreaming(false)
      }
    },
    [projectId, streaming, clearTimers, updateAssistant, pollUntilDone, refreshSessions],
  )

  const stop = useCallback(async () => {
    if (!projectId) return
    const runId = activeRunRef.current
    const assistantId = activeAssistantRef.current
    clearTimers()
    setStreaming(false)
    if (runId) {
      try {
        await projectsApi.cancelRun(projectId, runId)
      } catch {
        /* still mark stopped locally */
      }
    }
    if (assistantId) {
      updateAssistant(assistantId, {
        content: 'Stopped. Tell me what to change, or ask me to continue.',
        tools: undefined,
        kind: 'stopped',
        status: 'stopped',
      })
    }
    activeRunRef.current = null
  }, [projectId, clearTimers, updateAssistant])

  const resetSession = useCallback(async () => {
    if (!projectId || streaming) return
    clearTimers()
    const session = await projectsApi.resetSession(projectId)
    const list = await refreshSessions()
    setSessions(list)
    setActiveSessionId(session.id)
    setMessages([])
    setError(null)
  }, [projectId, streaming, clearTimers, refreshSessions])

  const selectSession = useCallback(
    async (sessionId: string) => {
      if (sessionId === activeSessionRef.current || streaming) return
      await loadSession(sessionId)
    },
    [loadSession, streaming],
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
          content: 'Draft saved. You can keep editing it here, or open it from Drafts / Editor.',
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
    sessions,
    activeSessionId,
    hydrating,
    streaming,
    error,
    send,
    stop,
    attach,
    saveDraft,
    updateDraft,
    resetSession,
    selectSession,
  }
}
