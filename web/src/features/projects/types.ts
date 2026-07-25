export type IndexStatus = 'pending' | 'indexed' | 'failed'

export type RunStatus = 'queued' | 'running' | 'succeeded' | 'failed'

export interface Project {
  id: string
  name: string
  description: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface ProjectAttachment {
  id: string
  project_id: string
  filename: string
  content_type: string
  size_bytes: number
  index_status: IndexStatus
  created_at: string
}

export interface ProjectRun {
  id: string
  project_id: string
  prompt: string
  status: RunStatus
  error: string | null
  arq_job_id: string | null
  created_at: string
  updated_at: string
  screenplay_preview?: string | null
  screenplay_md?: string | null
  draft_script_id?: string | null
  is_draft?: boolean
}

export interface ScriptLatest {
  id: string
  project_id: string
  run_id: string
  version: number
  package: Record<string, unknown>
  screenplay_md: string
  created_at: string
}

export interface ScriptSummary {
  id: string
  project_id: string
  run_id: string
  version: number
  title: string | null
  prompt_snippet: string | null
  created_at: string
}

export interface CreateProjectInput {
  name: string
  description?: string
}

export interface StartRunInput {
  prompt: string
  narration_config?: Record<string, unknown>
  part_count?: number
  total_duration_sec?: number
}
