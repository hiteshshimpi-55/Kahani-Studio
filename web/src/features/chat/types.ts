export type AgentToolStatus = 'pending' | 'running' | 'done' | 'error'

export type AgentToolStep = {
  id: string
  label: string
  detail?: string
  status: AgentToolStatus
}

export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: number
  tools?: AgentToolStep[]
  scriptPreview?: string
  scriptId?: string
  runId?: string
  isDraft?: boolean
  questions?: string[]
  kind?: 'user' | 'reply' | 'clarify' | 'generating' | 'script' | 'stopped'
  status?: 'streaming' | 'complete' | 'error' | 'stopped'
}

export const GRAPH_TOOL_STEPS: Omit<AgentToolStep, 'status'>[] = [
  { id: 'analyze', label: 'Analyze prompt', detail: 'Deciding chat vs audio generation' },
  { id: 'discovery', label: 'Discovery', detail: 'Gathering context → source.md' },
  { id: 'script_writer', label: 'Script Writer', detail: 'Outline → expand audio screenplay' },
  { id: 'persist', label: 'Write artifacts', detail: 'Saving screenplay package for review' },
]
