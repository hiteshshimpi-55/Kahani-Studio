import type { TimelineDoc } from './types'

const PREFIX = 'kahani.timeline.v1'

export function timelineStorageKey(projectId: string, draftId: string): string {
  return `${PREFIX}:${projectId}:${draftId}`
}

export function loadTimeline(projectId: string, draftId: string): TimelineDoc | null {
  try {
    const raw = localStorage.getItem(timelineStorageKey(projectId, draftId))
    if (!raw) return null
    const parsed = JSON.parse(raw) as TimelineDoc
    if (parsed?.version !== 1 || !Array.isArray(parsed.tracks)) return null
    return parsed
  } catch {
    return null
  }
}

export function saveTimeline(projectId: string, draftId: string, doc: TimelineDoc): void {
  try {
    localStorage.setItem(timelineStorageKey(projectId, draftId), JSON.stringify(doc))
  } catch {
    /* quota */
  }
}

export function clearTimeline(projectId: string, draftId: string): void {
  localStorage.removeItem(timelineStorageKey(projectId, draftId))
}
