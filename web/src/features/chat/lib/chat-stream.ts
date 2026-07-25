import { apiUrl } from '@/lib/api-client'

export type PlotPitch = {
  title: string
  logline: string
  tone: string
}

export type PitchResearchMeta = {
  extraction?: boolean
  tavily?: boolean
  topic?: string | null
  similar_works?: number
  sources?: number
}

export type ChatStreamEvent =
  | { type: 'start'; assistant_id: string; session_id: string }
  | { type: 'status'; phase: string; label: string; action?: string }
  | { type: 'text_delta'; delta: string }
  | { type: 'plot_pitches'; pitches: PlotPitch[]; research?: PitchResearchMeta }
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
      plot_pitches?: PlotPitch[]
      research?: PitchResearchMeta
      created_at: string
    }
  | { type: 'error'; message: string }

export type StreamChatHandlers = {
  onEvent: (event: ChatStreamEvent) => void
  signal?: AbortSignal
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException('Aborted', 'AbortError'))
      return
    }
    const t = window.setTimeout(resolve, ms)
    const onAbort = () => {
      window.clearTimeout(t)
      reject(new DOMException('Aborted', 'AbortError'))
    }
    signal?.addEventListener('abort', onAbort, { once: true })
  })
}

function parseBlock(block: string): ChatStreamEvent[] {
  const out: ChatStreamEvent[] = []
  for (const line of block.split(/\r?\n/)) {
    if (!line.startsWith('data:')) continue
    const raw = line.slice(5).trim()
    if (!raw) continue
    try {
      out.push(JSON.parse(raw) as ChatStreamEvent)
    } catch {
      /* skip malformed */
    }
  }
  return out
}

async function emitBatch(
  batch: ChatStreamEvent[],
  handlers: StreamChatHandlers,
): Promise<void> {
  if (!batch.length) return
  const pace = batch.filter((e) => e.type === 'text_delta').length > 1
  for (const evt of batch) {
    handlers.onEvent(evt)
    if (pace && evt.type === 'text_delta') {
      await sleep(20, handlers.signal)
    } else if (pace && evt.type === 'status') {
      await sleep(60, handlers.signal)
    }
  }
}

/**
 * POST + SSE body parser (fetch streaming, not EventSource — supports POST body).
 *
 * sse-starlette emits CRLF (`\r\n\r\n`) frame separators — must not split on `\n\n` only.
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

  const flushFrames = async (chunk: string, { final = false } = {}) => {
    buffer += chunk
    buffer = buffer.replace(/\r\n/g, '\n').replace(/\r/g, '\n')

    const parts = buffer.split('\n\n')
    buffer = final ? '' : (parts.pop() ?? '')

    const batch: ChatStreamEvent[] = []
    for (const block of parts) {
      batch.push(...parseBlock(block))
    }
    if (final && buffer.trim()) {
      batch.push(...parseBlock(buffer))
      buffer = ''
    }
    await emitBatch(batch, handlers)
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      await flushFrames(decoder.decode(), { final: true })
      break
    }
    await flushFrames(decoder.decode(value, { stream: true }))
  }
}
