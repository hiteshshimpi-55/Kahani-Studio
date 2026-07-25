import { apiUrl, parseJson } from '@/lib/api-client'

export type TtsClipRequest = {
  clip_id: string
  text: string
  voice_id: string
}

export type TtsClipResult = {
  clip_id: string
  audio_url: string
  duration_hint_sec?: number
  stub?: boolean
}

export async function synthesizeClip(
  projectId: string,
  body: TtsClipRequest,
): Promise<TtsClipResult> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/timeline/tts`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return parseJson<TtsClipResult>(res)
}

export async function synthesizeClipsBatch(
  projectId: string,
  clips: TtsClipRequest[],
): Promise<{ results: TtsClipResult[]; errors: { clip_id: string; error: string }[] }> {
  const res = await fetch(apiUrl(`/api/v1/projects/${projectId}/timeline/tts/batch`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ clips }),
  })
  return parseJson(res)
}
