import { apiUrl, parseJson } from '@/lib/api-client'

import type {
  CreateProjectInput,
  Project,
  ProjectAttachment,
  ProjectRun,
  ScriptLatest,
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

export async function getRun(projectId: string, runId: string): Promise<ProjectRun> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/runs/${runId}`))
  return parseJson(res)
}

export async function getLatestScript(projectId: string): Promise<ScriptLatest> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/scripts/latest`))
  return parseJson(res)
}
