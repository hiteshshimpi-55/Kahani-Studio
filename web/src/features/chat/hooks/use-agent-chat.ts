import { useCallback, useEffect, useRef, useState } from 'react'

import * as projectsApi from '@/features/projects/api/projects-api'
import type { ChatSession, ProjectAttachment } from '@/features/projects/types'

import { streamChatMessage } from '../lib/chat-stream'
import type { PlotPitch } from '../lib/chat-stream'
import {
  REWRITE_PHRASES,
  WRITING_PHRASES,
  type ChatActivity,
  type ChatMessage,
} from '../types'

function uid(): string {
  return crypto.randomUUID()
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
        activity: { phase: 'writing', label: WRITING_PHRASES[0]! },
        status: 'streaming' as const,
      }
    }

    const msg: ChatMessage = {
      id: item.id,
      role: 'assistant' as const,
      content: item.content,
      createdAt,
      kind: (item.kind as ChatMessage['kind']) || 'reply',
      questions: item.questions,
      plotPitches: item.plot_pitches ?? undefined,
      runId: item.run_id ?? undefined,
      scriptPreview: item.script_preview ?? undefined,
      scriptId: item.draft_script_id ?? undefined,
      isDraft: Boolean(item.is_draft),
      status: 'complete' as const,
    }
    return msg
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
  const phraseRef = useRef<number | null>(null)
  const abortRef = useRef<AbortController | null>(null)
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
    if (phraseRef.current) {
      window.clearInterval(phraseRef.current)
      phraseRef.current = null
    }
    abortRef.current?.abort()
    abortRef.current = null
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

  const startPhraseRotation = useCallback(
    (assistantId: string, action?: ChatMessage['action']) => {
      if (phraseRef.current) window.clearInterval(phraseRef.current)
      const pool = action === 'rewrite' ? REWRITE_PHRASES : WRITING_PHRASES
      let idx = 0
      phraseRef.current = window.setInterval(() => {
        idx = (idx + 1) % pool.length
        updateAssistant(assistantId, {
          activity: { phase: action === 'rewrite' ? 'rewriting' : 'writing', label: pool[idx]! },
        })
      }, 3200)
    },
    [updateAssistant],
  )

  const pollUntilDone = useCallback(
    (assistantId: string, runId: string, action?: ChatMessage['action']) => {
      if (!projectId) return Promise.resolve()
      activeRunRef.current = runId
      activeAssistantRef.current = assistantId
      startPhraseRotation(assistantId, action)

      return new Promise<void>((resolve) => {
        pollRef.current = window.setInterval(async () => {
          try {
            const next = await projectsApi.getRun(projectId, runId)
            if (next.status === 'succeeded') {
              clearTimers()
              const preview = next.screenplay_md || next.screenplay_preview || ''
              updateAssistant(assistantId, {
                activity: null,
                content:
                  'Your script is ready. Review it below — save as a draft when you want to keep it.',
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
                activity: null,
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
                activity: null,
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
    [projectId, clearTimers, updateAssistant, refreshSessions, startPhraseRotation],
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
          await pollUntilDone(inFlight.id, inFlight.runId)
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load chat')
      } finally {
        setHydrating(false)
      }
    },
    [projectId, clearTimers, pollUntilDone],
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
      clearTimers()

      const userMsg: ChatMessage = {
        id: uid(),
        role: 'user',
        content: text.trim(),
        createdAt: Date.now(),
        kind: 'user',
        status: 'complete',
      }
      const assistantId = uid()
      setMessages((prev) => [
        ...prev,
        userMsg,
        {
          id: assistantId,
          role: 'assistant',
          content: '',
          createdAt: Date.now(),
          activity: { phase: 'thinking', label: 'Reading your message…' },
          status: 'streaming',
          kind: 'reply',
        },
      ])
      setStreaming(true)

      const controller = new AbortController()
      abortRef.current = controller
      activeAssistantRef.current = assistantId

      let content = ''
      let finalId: string = assistantId
      let runId: string | undefined
      let kind: ChatMessage['kind'] = 'reply'
      let action: ChatMessage['action']
      let questions: string[] = []
      // Mutated inside onEvent; TS CFA does not see those writes after await.
      let shouldPollGeneration = false

      const patchStreaming = (patch: Partial<ChatMessage>) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId || m.id === finalId ? { ...m, ...patch } : m,
          ),
        )
      }

      try {
        await streamChatMessage(projectId, text.trim(), activeSessionRef.current ?? undefined, {
          signal: controller.signal,
          onEvent: (evt) => {
            if (evt.type === 'start') {
              if (evt.session_id !== activeSessionRef.current) {
                setActiveSessionId(evt.session_id)
              }
              return
            }
            if (evt.type === 'status') {
              // Don't flash status over an in-progress typewriter.
              // Writing/rewriting status after run_started is allowed (runId set).
              if (content.length > 0 && !runId) return
              patchStreaming({
                activity: {
                  phase: evt.phase as ChatActivity['phase'],
                  label: evt.label,
                },
                action: (evt.action as ChatMessage['action']) ?? action,
              })
              if (evt.action) action = evt.action as ChatMessage['action']
              return
            }
            if (evt.type === 'text_delta') {
              content += evt.delta
              patchStreaming({ content, activity: null })
              return
            }
            if (evt.type === 'plot_pitches') {
              const pitches = (evt as { type: 'plot_pitches'; pitches: PlotPitch[] }).pitches
              patchStreaming({ plotPitches: pitches })
              return
            }
            if (evt.type === 'run_started') {
              finalId = evt.id
              runId = evt.run_id
              kind = 'generating'
              shouldPollGeneration = true
              action = evt.action as ChatMessage['action']
              content = evt.content
              patchStreaming({ id: finalId, runId, kind, content, action })
              activeAssistantRef.current = finalId
              return
            }
            if (evt.type === 'done') {
              finalId = evt.id
              kind = evt.kind as ChatMessage['kind']
              content = evt.content
              questions = evt.questions ?? []
              runId = evt.run_id
              action = evt.action as ChatMessage['action']
              shouldPollGeneration = evt.kind === 'generating' && Boolean(evt.run_id)
              if (evt.session_id) setActiveSessionId(evt.session_id)
              const donePitches = (evt as { plot_pitches?: PlotPitch[] }).plot_pitches
              patchStreaming({
                id: finalId,
                content,
                kind,
                questions,
                runId,
                action,
                plotPitches: donePitches ?? undefined,
                activity: shouldPollGeneration ? undefined : null,
                status: shouldPollGeneration ? 'streaming' : 'complete',
              })
              activeAssistantRef.current = finalId
            }
          },
        })

        if (runId && shouldPollGeneration) {
          updateAssistant(finalId, {
            content,
            kind: 'generating',
            runId,
            action,
            activity: {
              phase: action === 'rewrite' ? 'rewriting' : 'writing',
              label: action === 'rewrite' ? REWRITE_PHRASES[0]! : WRITING_PHRASES[0]!,
            },
            status: 'streaming',
          })
          await pollUntilDone(finalId, runId, action)
          return
        }

        updateAssistant(finalId, {
          id: finalId,
          content,
          kind,
          questions,
          action,
          activity: null,
          status: 'complete',
        })
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId || m.id === finalId
              ? {
                  ...m,
                  id: finalId,
                  content,
                  kind,
                  questions,
                  activity: null,
                  status: 'complete' as const,
                }
              : m,
          ),
        )
        setStreaming(false)
        void refreshSessions()
      } catch (e) {
        if (controller.signal.aborted) return
        clearTimers()
        const msg = e instanceof Error ? e.message : 'Failed to send message'
        setError(msg)
        updateAssistant(finalId, {
          content: msg,
          activity: null,
          status: 'error',
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
        activity: null,
        kind: 'stopped',
        status: 'stopped',
      })
    }
    activeRunRef.current = null
  }, [projectId, clearTimers, updateAssistant])

  const addSession = useCallback(async () => {
    if (!projectId || streaming) return
    clearTimers()
    const session = await projectsApi.createSession(projectId)
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
        const att = await projectsApi.uploadAttachment(projectId, file)
        setMessages((prev) => [
          ...prev,
          {
            id: uid(),
            role: 'assistant',
            content: `Added “${att.filename}” to project context. I'll use it when we write or revise your script.`,
            createdAt: Date.now(),
            kind: 'context',
            status: 'complete',
          },
        ])
        return att
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
    addSession,
    selectSession,
  }
}
