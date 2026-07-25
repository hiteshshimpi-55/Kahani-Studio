import { apiUrl, parseJson } from '@/lib/api-client'

import type {
  ChatSession,
  CreateProjectInput,
  Project,
  ProjectAttachment,
  ProjectRun,
  ScriptLatest,
  ScriptSummary,
  StartRunInput,
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

export async function resetSession(projectId: string): Promise<ChatSession> {
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
    script_preview?: string | null
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
