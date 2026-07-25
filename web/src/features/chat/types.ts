export type ChatActivityPhase =
  | 'thinking'
  | 'figuring'
  | 'context'
  | 'writing'
  | 'rewriting'
  | 'polishing'
  | 'idle'

export type ChatActivity = {
  phase: ChatActivityPhase
  label: string
}

export type ChatAction = 'chat' | 'clarify' | 'generate' | 'rewrite' | 'context_note'

export type AgentToolStep = {
  id: string
  label: string
  detail?: string
  status: 'pending' | 'running' | 'done' | 'error'
}

export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: number
  activity?: ChatActivity | null
  scriptPreview?: string
  scriptId?: string
  runId?: string
  isDraft?: boolean
  questions?: string[]
  kind?: 'user' | 'reply' | 'clarify' | 'generating' | 'script' | 'stopped' | 'context'
  status?: 'streaming' | 'complete' | 'error' | 'stopped'
  action?: ChatAction
}

/** Rotating labels while a generation run is in flight (client-side only). */
export const WRITING_PHRASES = [
  'Writing your script…',
  'Shaping dialogue and beats…',
  'Drafting the audio screenplay…',
  'Building episode structure…',
  'Almost there…',
]

export const REWRITE_PHRASES = [
  'Reworking the script…',
  'Applying your notes…',
  'Revising the draft…',
  'Polishing the new version…',
]
