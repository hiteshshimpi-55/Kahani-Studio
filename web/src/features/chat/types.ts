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
  status?: 'streaming' | 'complete' | 'error'
}

export const GRAPH_TOOL_STEPS: Omit<AgentToolStep, 'status'>[] = [
  { id: 'retrieve_context', label: 'Retrieve context', detail: 'Searching project attachments' },
  { id: 'build_source', label: 'Build source brief', detail: 'Assembling source.md from prompt + RAG' },
  { id: 'script_writer', label: 'Script Writer', detail: 'Outline → expand audio screenplay' },
  { id: 'persist', label: 'Write artifacts', detail: 'Saving screenplay package for review' },
]
