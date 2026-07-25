// Audience simulation domain types matching backend schemas

export interface AuditScore {
  name: string
  score: number
  comment: string
}

export interface StructuralAudit {
  overall_score: number
  hook_score: AuditScore
  pacing_score: AuditScore
  dialogue_score: AuditScore
  cliffhanger_score: AuditScore
}

export interface PartFunnel {
  part: number
  start_rate: number
  p_continue: number
  drop_reasons: string[]
  fragile_beats: string[]
  cohort_disagreements: string[]
}

export interface EngagementReport {
  persona_count: number
  calibration_status: string
  funnel: PartFunnel[]
}

export interface Patch {
  id: string
  beat_id: string
  part: number
  patch_type: string
  rationale: string
  suggested_text: string | null
  expected_delta: Record<string, string> | null
  status: 'PENDING' | 'ACCEPTED' | 'REJECTED'
}

export interface SimRun {
  id: string
  episode_id: string
  series_id: string
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'
  calibration_status: string
  persona_count: number | null
  created_at: string
  audit: StructuralAudit | null
  engagement: EngagementReport | null
  patches: Patch[]
  error: string | null
}

export interface SimRunSummary {
  id: string
  episode_id: string
  series_id: string
  status: string
  calibration_status: string
  persona_count: number | null
  created_at: string
}

export interface SimulateRequest {
  episode_id: string
  series_id: string
  script: string
  language: string
  genre: string
  title: string
  part_count: number
}

export interface EnqueueSimResponse {
  sim_run_id: string
  queued: boolean
}
