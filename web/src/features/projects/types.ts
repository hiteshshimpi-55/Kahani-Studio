export type IndexStatus = 'pending' | 'indexed' | 'failed'

export type RunStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled'

export type ProductionStage = 'script' | 'audio' | 'cover_art' | 'assembly' | 'complete'

export type StageStatus =
  | 'idle'
  | 'generating'
  | 'pending_approval'
  | 'approved'
  | 'rejected'
  | 'failed'

export interface RunArtifacts {
  screenplay_key?: string | null
  package_key?: string | null
  audio_key?: string | null
  cover_key?: string | null
  manifest_key?: string | null
  audio_url?: string | null
  cover_url?: string | null
  visuals_series_id?: string | null
  visuals_url?: string | null
}

export interface VisualEpisodeStatus {
  series_id: string
  status: string
  plan?: {
    title?: string
    characters?: Array<{
      id?: string
      name?: string
      reference_image?: string | null
    }>
    shots?: Array<{
      shot_id?: string
      scene_id?: string
      prompt_brief?: string
      t_start?: number
      t_end?: number
    }>
  } | null
  lookbook?: Record<string, string>
  stills?: Record<string, string>
  video_url?: string | null
  shot_count?: number
  characters_ready?: boolean
  duration_sec?: number | null
}

export interface RunProgress {
  total_lines?: number | null
  lines_rendered?: number | null
  duration_sec?: number | null
  current_step?: string | null
}

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
  session_id?: string | null
  part_count?: number | null
  total_duration_sec?: number | null
  screenplay_preview?: string | null
  screenplay_md?: string | null
  package?: ScriptPackage | null
  draft_script_id?: string | null
  is_draft?: boolean
  current_stage?: ProductionStage | string | null
  stage_statuses?: Partial<Record<ProductionStage | string, StageStatus | string>> | null
  artifacts?: RunArtifacts | null
  progress?: RunProgress | null
  revision_notes?: string | null
}

export interface BibleCharacter {
  id?: string
  name?: string
  role?: string
  voice?: string
  speech_patterns?: string
  arc?: string
}

export interface ScriptPackage {
  title?: string
  language?: string
  narration_config?: Record<string, unknown>
  bible?: { characters?: BibleCharacter[] }
  parts?: Array<{
    part_number?: number
    title?: string
    target_duration_sec?: number
    screenplay?: string
    cliff_out?: string
    sfx_cues?: string[]
  }>
  total_duration_sec?: number
  [key: string]: unknown
}

export interface ProjectCharacter {
  id: string
  project_id: string
  character_key: string
  name: string
  role: string | null
  voice: string | null
  speech_patterns: string | null
  arc: string | null
  created_at: string
  updated_at: string
}

export interface StoryContextSummary {
  cast_count: number
  docs_count: number
  episode_count: number
  latest_part_number: number | null
}

export interface ChatSession {
  id: string
  project_id: string
  title: string
  created_at: string
  updated_at: string
  run_count: number
}

export interface ScriptLatest {
  id: string
  project_id: string
  run_id: string
  version: number
  package: ScriptPackage
  screenplay_md: string
  created_at: string
  part_number?: number | null
  pinned?: boolean
  cliff_out?: string | null
  title?: string | null
}

export interface ScriptSummary {
  id: string
  project_id: string
  run_id: string
  version: number
  title: string | null
  prompt_snippet: string | null
  created_at: string
  part_number?: number | null
  pinned?: boolean
  cliff_out?: string | null
  is_latest_continuity?: boolean
}

export interface CreateProjectInput {
  name: string
  description?: string
}

export interface StartRunInput {
  prompt: string
  session_id?: string
  narration_config?: Record<string, unknown>
  part_count?: number
  total_duration_sec?: number
  part_number?: number
}
