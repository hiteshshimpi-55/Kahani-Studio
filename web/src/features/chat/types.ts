export type ChatActivityPhase =
  | 'thinking'
  | 'figuring'
  | 'context'
  | 'discovering'
  | 'writing'
  | 'rewriting'
  | 'polishing'
  | 'idle'

export type ChatActivity = {
  phase: ChatActivityPhase
  label: string
}

export type ChatAction = 'chat' | 'discover' | 'generate' | 'rewrite' | 'context_note'

export type PlotPitch = {
  title: string
  logline: string
  tone: string
}

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
  plotPitches?: PlotPitch[]
  kind?: 'user' | 'reply' | 'discover' | 'clarify' | 'generating' | 'script' | 'stopped' | 'context'
  status?: 'streaming' | 'complete' | 'error' | 'stopped'
  action?: ChatAction
}

/** Rotating labels while a generation run is in flight (client-side only). */
export const WRITING_PHRASES = [
  'Writing your script…',
  'Shaping the opening beat…',
  'Finding the right voice…',
  'Drafting dialogue and turns…',
  'Building the episode arc…',
  'Letting the story breathe…',
  'Threading the cliffhangers…',
  'Almost there…',
]

export const REWRITE_PHRASES = [
  'Reworking the script…',
  'Applying your notes…',
  'Revising the draft…',
  'Tightening the beats…',
  'Reshaping what you flagged…',
  'Polishing the new version…',
]
