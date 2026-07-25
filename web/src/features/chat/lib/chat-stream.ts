import { apiUrl } from '@/lib/api-client'

export type ChatStreamEvent =
  | { type: 'start'; assistant_id: string; session_id: string }
  | { type: 'status'; phase: string; label: string; action?: string }
  | { type: 'text_delta'; delta: string }
  | {
      type: 'run_started'
      id: string
      run_id: string
      kind: string
      content: string
      session_id: string
      action?: string
      created_at: string
    }
  | {
      type: 'done'
      id: string
      kind: string
      content: string
      session_id: string
      run_id?: string
      questions?: string[]
      action?: string
      created_at: string
    }
  | { type: 'error'; message: string }

export type StreamChatHandlers = {
  onEvent: (event: ChatStreamEvent) => void
  signal?: AbortSignal
}

/**
 * POST + SSE body parser (fetch streaming, not EventSource — supports POST body).
 */
export async function streamChatMessage(
  projectId: string,
  message: string,
  sessionId: string | undefined,
  handlers: StreamChatHandlers,
): Promise<void> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/chat/messages/stream`), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({ message, session_id: sessionId ?? null }),
    signal: handlers.signal,
  })

  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const body = (await res.json()) as { message?: string; detail?: string }
      detail = body.message || body.detail || detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }

  const reader = res.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''

    for (const block of parts) {
      for (const line of block.split('\n')) {
        if (!line.startsWith('data:')) continue
        const raw = line.slice(5).trim()
        if (!raw) continue
        try {
          handlers.onEvent(JSON.parse(raw) as ChatStreamEvent)
        } catch {
          /* skip malformed */
        }
      }
    }
  }
}
