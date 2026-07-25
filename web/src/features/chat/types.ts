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

export type PitchResearchMeta = {
  extraction?: boolean
  tavily?: boolean
  topic?: string | null
  similar_works?: number
  sources?: number
}

export type AgentToolStep = {
  id: string
  label: string
  detail?: string
  status: 'pending' | 'running' | 'done' | 'error'
}

export type ScriptPackagePreview = {
  title?: string
  bible?: {
    characters?: Array<{
      id?: string
      name?: string
      role?: string
      voice?: string
      speech_patterns?: string
      arc?: string
    }>
  }
  parts?: Array<{
    part_number?: number
    title?: string
    cliff_out?: string
  }>
}

export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: number
  activity?: ChatActivity | null
  scriptPreview?: string
  scriptPackage?: ScriptPackagePreview | null
  scriptId?: string
  runId?: string
  isDraft?: boolean
  questions?: string[]
  plotPitches?: PlotPitch[]
  pitchResearch?: PitchResearchMeta | null
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
