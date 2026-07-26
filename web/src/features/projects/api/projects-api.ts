import { apiUrl, parseJson } from '@/lib/api-client'

import type {
  ChatSession,
  CreateProjectInput,
  Project,
  ProjectAttachment,
  ProjectCharacter,
  ProjectRun,
  ScriptLatest,
  ScriptSummary,
  StartRunInput,
  StoryContextSummary,
  VisualEpisodeStatus,
} from '../types'

export async function listProjects(): Promise<Project[]> {
  const res = await fetch(apiUrl('/api/v1/projects'))
  return parseJson(res)
}

export async function getProject(projectId: string): Promise<Project> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}`))
  return parseJson(res)
}

export async function createProject(input: CreateProjectInput): Promise<Project> {
  const res = await fetch(apiUrl('/api/v1/projects'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  return parseJson(res)
}

export async function deleteProject(projectId: string): Promise<void> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}`), { method: 'DELETE' })
  if (!res.ok && res.status !== 204) {
    await parseJson(res)
  }
}

export async function listSessions(projectId: string): Promise<ChatSession[]> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/sessions`))
  return parseJson(res)
}

export async function createSession(projectId: string): Promise<ChatSession> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/sessions`), {
    method: 'POST',
  })
  return parseJson(res)
}

export async function listAttachments(projectId: string): Promise<ProjectAttachment[]> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/attachments`))
  return parseJson(res)
}

export async function uploadAttachment(
  projectId: string,
  file: File,
): Promise<ProjectAttachment> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/attachments`), {
    method: 'POST',
    body: form,
  })
  return parseJson(res)
}

export async function deleteAttachment(
  projectId: string,
  attachmentId: string,
): Promise<void> {
  const res = await fetch(
    apiUrl(`/api/v1/projects/${projectId}/attachments/${attachmentId}`),
    { method: 'DELETE' },
  )
  if (!res.ok && res.status !== 204) {
    await parseJson(res)
  }
}

export async function startRun(
  projectId: string,
  input: StartRunInput,
): Promise<ProjectRun> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/runs`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  return parseJson(res)
}

export async function postChatMessage(
  projectId: string,
  message: string,
  sessionId?: string,
): Promise<{
  id: string
  role: string
  content: string
  kind: string
  created_at: string
  run_id?: string | null
  questions?: string[]
  session_id?: string | null
  run?: ProjectRun | null
}> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/chat/messages`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId ?? null }),
  })
  return parseJson(res)
}

export async function listChatMessages(
  projectId: string,
  sessionId?: string,
): Promise<
  Array<{
    id: string
    role: string
    content: string
    kind: string
    created_at: string
    run_id?: string | null
    questions?: string[]
    plot_pitches?: Array<{ title: string; logline: string; tone: string }>
    script_preview?: string | null
    script_package?: Record<string, unknown> | null
    draft_script_id?: string | null
    is_draft?: boolean
    run_status?: string | null
  }>
> {
  const qs = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/chat/messages${qs}`))
  return parseJson(res)
}

export async function cancelRun(projectId: string, runId: string): Promise<ProjectRun> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/runs/${runId}/cancel`), {
    method: 'POST',
  })
  return parseJson(res)
}

export async function listRuns(
  projectId: string,
  sessionId?: string,
): Promise<ProjectRun[]> {
  const qs = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/runs${qs}`))
  return parseJson(res)
}

export async function getRun(projectId: string, runId: string): Promise<ProjectRun> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/runs/${runId}`))
  return parseJson(res)
}

export async function approveStage(
  projectId: string,
  runId: string,
  stage: string,
): Promise<ProjectRun> {
  const res = await fetch(
    apiUrl(`/api/v1/projects/${projectId}/runs/${runId}/stages/${stage}/approve`),
    { method: 'POST' },
  )
  return parseJson(res)
}

export async function rejectStage(
  projectId: string,
  runId: string,
  stage: string,
  body: { action: 'regenerate' | 'revise'; notes?: string },
): Promise<ProjectRun> {
  const res = await fetch(
    apiUrl(`/api/v1/projects/${projectId}/runs/${runId}/stages/${stage}/reject`),
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
  )
  return parseJson(res)
}

export async function startRunVisuals(
  projectId: string,
  runId: string,
): Promise<ProjectRun> {
  const res = await fetch(
    apiUrl(`/api/v1/projects/${projectId}/runs/${runId}/visuals/start`),
    { method: 'POST' },
  )
  return parseJson(res)
}

export async function skipRunVisuals(
  projectId: string,
  runId: string,
): Promise<ProjectRun> {
  const res = await fetch(
    apiUrl(`/api/v1/projects/${projectId}/runs/${runId}/visuals/skip`),
    { method: 'POST' },
  )
  return parseJson(res)
}

export async function getVisualEpisode(seriesId: string): Promise<VisualEpisodeStatus> {
  const res = await fetch(apiUrl(`/api/v1/visuals/${encodeURIComponent(seriesId)}`))
  return parseJson(res)
}

export async function saveRunAsDraft(
  projectId: string,
  runId: string,
  screenplay_md?: string,
): Promise<ScriptLatest> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/runs/${runId}/draft`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(screenplay_md != null ? { screenplay_md } : {}),
  })
  return parseJson(res)
}

export async function getLatestScript(projectId: string): Promise<ScriptLatest> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/scripts/latest`))
  return parseJson(res)
}

export async function listScripts(projectId: string): Promise<ScriptSummary[]> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/scripts`))
  return parseJson(res)
}

export async function pinScript(
  projectId: string,
  scriptId: string,
  pinned: boolean,
): Promise<ScriptSummary> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/scripts/${scriptId}/pin`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pinned }),
  })
  return parseJson(res)
}

export async function listCharacters(projectId: string): Promise<ProjectCharacter[]> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/characters`))
  return parseJson(res)
}

export async function updateCharacter(
  projectId: string,
  characterId: string,
  body: Partial<
    Pick<ProjectCharacter, 'name' | 'role' | 'voice' | 'speech_patterns' | 'arc'>
  >,
): Promise<ProjectCharacter> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/characters/${characterId}`), {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return parseJson(res)
}

export async function deleteCharacter(
  projectId: string,
  characterId: string,
): Promise<void> {
  const res = await fetch(
    apiUrl(`/api/v1/projects/${projectId}/characters/${characterId}`),
    { method: 'DELETE' },
  )
  if (!res.ok && res.status !== 204) {
    await parseJson(res)
  }
}

export async function getStoryContextSummary(
  projectId: string,
): Promise<StoryContextSummary> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/story-context`))
  return parseJson(res)
}

export async function getScript(projectId: string, scriptId: string): Promise<ScriptLatest> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/scripts/${scriptId}`))
  return parseJson(res)
}

export async function updateScript(
  projectId: string,
  scriptId: string,
  screenplay_md: string,
): Promise<ScriptLatest> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/scripts/${scriptId}`), {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ screenplay_md }),
  })
  return parseJson(res)
}

export type ScriptAudioStatus = {
  script_id: string
  project_id: string
  status: 'idle' | 'queued' | 'running' | 'succeeded' | 'failed' | string
  error?: string | null
  audio_url?: string | null
  voice_provider?: string | null
  line_count?: number | null
  sfx_clip_count?: number | null
  title?: string | null
  updated_at?: string | null
}

export async function generateScriptAudio(
  projectId: string,
  scriptId: string,
  opts?: { max_sec?: number; voice_provider?: string },
): Promise<ScriptAudioStatus> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/scripts/${scriptId}/audio`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      max_sec: opts?.max_sec ?? 300,
      voice_provider: opts?.voice_provider ?? 'elevenlabs',
      with_sfx: true,
      with_bed: true,
    }),
  })
  return parseJson(res)
}

export async function getScriptAudioStatus(
  projectId: string,
  scriptId: string,
): Promise<ScriptAudioStatus> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/scripts/${scriptId}/audio`))
  return parseJson(res)
}

export interface ExportResult {
  url: string
  filename: string
  expires_in: number | null
}

export async function exportScript(
  projectId: string,
  scriptId: string,
  format: 'markdown' | 'audio' | 'cover',
): Promise<ExportResult> {
  const res = await fetch(
    apiUrl(`/api/v1/projects/${projectId}/scripts/${scriptId}/export`),
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ format }),
    },
  )
  return parseJson(res)
}
